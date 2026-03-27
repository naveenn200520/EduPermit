from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from models import db, User, Department, Permission, Bonafide, Attendance, Notification
from gate_pass import generate_gate_pass_qr
from datetime import datetime
import os
import secrets
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError


def create_app():
    app = Flask(__name__)
    
    # Configuration for production/development
    app.secret_key = os.environ.get('SECRET_KEY', 'college_mgmt_secret_2024_xK9mP')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///college.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure upload folder for profile photos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'profiles')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    db.init_app(app)
    return app


app = create_app()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Unauthorized access.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


def add_notification(user_id, message, notif_type='info'):
    n = Notification(user_id=user_id, message=message, notif_type=notif_type)
    db.session.add(n)
    db.session.commit()


# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))
    if request.method == 'POST':
        role = request.form.get('role')
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()

        user = None
        if role == 'student':
            user = User.query.filter_by(reg_no=identifier, role='student').first()
        else:
            if identifier:
                user = User.query.filter(
                    User.email == identifier, User.role == role
                ).first()

        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            session['photo'] = getattr(user, 'photo', 'default.png')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for(f"{user.role}_dashboard"))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─── Student Routes ───────────────────────────────────────────────────────────

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    user = get_current_user()
    perms = Permission.query.filter_by(student_id=user.id).all()
    total = len(perms)
    pending = sum(1 for p in perms if p.status == 'pending')
    approved = sum(1 for p in perms if p.status == 'approved')
    rejected = sum(1 for p in perms if p.status == 'rejected')
    recent = Permission.query.filter_by(student_id=user.id).order_by(Permission.created_at.desc()).limit(5).all()
    attendance = Attendance.query.filter_by(student_id=user.id).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('student/dashboard.html', user=user, total=total, pending=pending,
                           approved=approved, rejected=rejected, recent=recent,
                           attendance=attendance, notif_count=notifs)


@app.route('/student/apply', methods=['GET', 'POST'])
@login_required(role='student')
def student_apply():
    user = get_current_user()
    if request.method == 'POST':
        p = Permission(
            student_id=user.id,
            perm_type=request.form['perm_type'],
            from_date=request.form['from_date'],
            to_date=request.form['to_date'],
            from_time=request.form.get('from_time'),
            to_time=request.form.get('to_time'),
            reason=request.form['reason'],
            status='pending'
        )
        db.session.add(p)
        db.session.commit()
        add_notification(user.id, f"Your {p.perm_type} request has been submitted successfully.", "info")
        flash('Permission request submitted successfully!', 'success')
        return redirect(url_for('student_history'))
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('student/apply_permission.html', user=user, notif_count=notifs)


@app.route('/student/bonafide', methods=['GET', 'POST'])
@login_required(role='student')
def student_bonafide():
    user = get_current_user()
    if request.method == 'POST':
        b = Bonafide(student_id=user.id, purpose=request.form['purpose'], status='pending')
        db.session.add(b)
        db.session.commit()
        add_notification(user.id, "Your bonafide certificate request has been submitted.", "info")
        flash('Bonafide request submitted!', 'success')
        return redirect(url_for('student_bonafide'))
    bonafides = Bonafide.query.filter_by(student_id=user.id).order_by(Bonafide.created_at.desc()).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('student/bonafide.html', user=user, bonafides=bonafides, notif_count=notifs)


@app.route('/student/bonafide/view/<int:bon_id>')
@login_required(role='student')
def view_bonafide(bon_id):
    user = get_current_user()
    bon = db.get_or_404(Bonafide, bon_id)
    
    # Security: Check if user has permission to view this certificate
    if user.role == 'student' and bon.student_id != user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    if bon.status != 'approved':
        flash('This certificate is not yet approved.', 'warning')
        return redirect(url_for('student_bonafide'))
        
    student = db.session.get(User, bon.student_id)
    return render_template('bonafide_certificate.html', bonafide=bon, student=student)


@app.route('/student/attendance')
@login_required(role='student')
def student_attendance():
    user = get_current_user()
    attendance = Attendance.query.filter_by(student_id=user.id).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('student/attendance.html', user=user, attendance=attendance, notif_count=notifs)


@app.route('/student/history')
@login_required(role='student')
def student_history():
    user = get_current_user()
    perms = Permission.query.filter_by(student_id=user.id).order_by(Permission.created_at.desc()).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('student/history.html', user=user, perms=perms, notif_count=notifs)


@app.route('/student/permission_letter/<int:perm_id>')
@login_required(role='student')
def view_permission_letter(perm_id):
    user = get_current_user()
    perm = db.get_or_404(Permission, perm_id)
    
    # Security: Check if user has permission to view this letter
    if user.role == 'student' and perm.student_id != user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    if perm.status != 'approved':
        flash('This permission is not yet approved.', 'warning')
        return redirect(url_for('student_history'))
        
    return render_template('permission_letter.html', perm=perm, student=perm.student)


@app.route('/student/notifications')
@login_required(role='student')
def student_notifications():
    user = get_current_user()
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('student/notifications.html', user=user, notifications=notifs, notif_count=0)


@app.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    user = get_current_user()
    if request.method == 'POST':
        # Handle Photo Upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext in ['png', 'jpg', 'jpeg', 'webp']:
                    filename = f"user_{user.id}_{secrets.token_hex(4)}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    user.photo = filename

        user.name = request.form.get('name', user.name)
        new_email = request.form.get('email', '').strip()
        if new_email:
            user.email = new_email
        
        user.phone = request.form.get('phone', user.phone)
        if request.form.get('new_password'):
            user.set_password(request.form['new_password'])
        db.session.commit()
        session['name'] = user.name
        session['photo'] = user.photo
        flash('Profile updated successfully!', 'success')
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('profile.html', user=user, notif_count=notifs)


# ─── Staff Routes ─────────────────────────────────────────────────────────────

@app.route('/staff/dashboard')
@login_required(role='staff')
def staff_dashboard():
    user = get_current_user()
    dept_students = User.query.filter_by(dept_id=user.dept_id, role='student').all()
    student_ids = [s.id for s in dept_students]
    pending = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'pending').count()
    approved = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'approved').count()
    forwarded = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.forwarded_to_hod == True).count()
    recent_requests = Permission.query.filter(Permission.student_id.in_(student_ids)).order_by(Permission.created_at.desc()).limit(8).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('staff/dashboard.html', user=user, pending=pending, approved=approved,
                           forwarded=forwarded, recent_requests=recent_requests,
                           total_students=len(dept_students), notif_count=notifs)


@app.route('/staff/requests')
@login_required(role='staff')
def staff_requests():
    user = get_current_user()
    dept_students = User.query.filter_by(dept_id=user.dept_id, role='student').all()
    student_ids = [s.id for s in dept_students]
    status_filter = request.args.get('status', 'all')
    query = Permission.query.filter(Permission.student_id.in_(student_ids))
    if status_filter != 'all':
        query = query.filter(Permission.status == status_filter)
    requests_list = query.order_by(Permission.created_at.desc()).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('staff/requests.html', user=user, requests=requests_list,
                           status_filter=status_filter, notif_count=notifs)


@app.route('/staff/approve/<int:perm_id>', methods=['POST'])
@login_required(role='staff')
def staff_approve(perm_id):
    user = get_current_user()
    perm = db.get_or_404(Permission, perm_id)
    action = request.form.get('action')
    remarks = request.form.get('remarks', '')

    perm.staff_id = user.id
    perm.staff_remarks = remarks
    perm.updated_at = datetime.utcnow()

    if action == 'approve':
        perm.status = 'approved'
        perm.qr_code_path = generate_gate_pass_qr(perm, perm.student, user.name, request.host_url)
        add_notification(perm.student_id, f"Your {perm.perm_type} request has been approved by {user.name}. Gate pass is ready!", "success")
        flash('Request approved and Gate Pass generated!', 'success')
    elif action == 'reject':
        perm.status = 'rejected'
        add_notification(perm.student_id, f"Your {perm.perm_type} request was rejected by {user.name}. Remarks: {remarks}", "danger")
        flash('Request rejected.', 'warning')
    elif action == 'forward':
        perm.status = 'forwarded'
        perm.forwarded_to_hod = True
        add_notification(perm.student_id, f"Your {perm.perm_type} request has been forwarded to HOD.", "warning")
        flash('Request forwarded to HOD.', 'info')

    db.session.commit()
    return redirect(url_for('staff_requests'))


@app.route('/staff/students')
@login_required(role='staff')
def staff_students():
    user = get_current_user()
    students = User.query.filter_by(dept_id=user.dept_id, role='student').order_by(User.year, User.section, User.name).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('staff/student_list.html', user=user, students=students, notif_count=notifs)


@app.route('/staff/attendance')
@login_required(role='staff')
def staff_attendance():
    user = get_current_user()
    students = User.query.filter_by(dept_id=user.dept_id, role='student').all()
    attendance_data = {}
    for s in students:
        att = Attendance.query.filter_by(student_id=s.id).all()
        if att:
            avg = sum(a.percentage for a in att) / len(att)
        else:
            avg = 0
        attendance_data[s.id] = {'student': s, 'avg': round(avg, 1), 'records': att}
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('staff/attendance.html', user=user, attendance_data=attendance_data, notif_count=notifs)


# ─── HOD Routes ───────────────────────────────────────────────────────────────

@app.route('/hod/dashboard')
@login_required(role='hod')
def hod_dashboard():
    user = get_current_user()
    dept_students = User.query.filter_by(dept_id=user.dept_id, role='student').all()
    student_ids = [s.id for s in dept_students]
    forwarded_perms = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.forwarded_to_hod == True, Permission.status == 'forwarded').count()
    total_perms = Permission.query.filter(Permission.student_id.in_(student_ids)).count()
    approved = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'approved').count()
    rejected = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'rejected').count()
    pending_bonafides = Bonafide.query.join(User, Bonafide.student_id == User.id).filter(User.dept_id == user.dept_id, Bonafide.status == 'pending').count()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('hod/dashboard.html', user=user, forwarded_perms=forwarded_perms,
                           total_perms=total_perms, approved=approved, rejected=rejected,
                           pending_bonafides=pending_bonafides,
                           total_students=len(dept_students), notif_count=notifs)


@app.route('/hod/approvals')
@login_required(role='hod')
def hod_approvals():
    user = get_current_user()
    dept_students = User.query.filter_by(dept_id=user.dept_id, role='student').all()
    student_ids = [s.id for s in dept_students]
    forwarded = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.forwarded_to_hod == True).order_by(Permission.created_at.desc()).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('hod/approvals.html', user=user, forwarded=forwarded, notif_count=notifs)


@app.route('/hod/approve/<int:perm_id>', methods=['POST'])
@login_required(role='hod')
def hod_approve(perm_id):
    user = get_current_user()
    perm = db.get_or_404(Permission, perm_id)
    action = request.form.get('action')
    remarks = request.form.get('remarks', '')
    perm.hod_remarks = remarks
    perm.updated_at = datetime.utcnow()

    if action == 'approve':
        perm.status = 'approved'
        perm.qr_code_path = generate_gate_pass_qr(perm, perm.student, f"HOD {user.name}", request.host_url)
        add_notification(perm.student_id, f"Your {perm.perm_type} request has been approved by HOD {user.name}. Gate pass ready!", "success")
        flash('Permission approved and Gate Pass generated!', 'success')
    elif action == 'reject':
        perm.status = 'rejected'
        add_notification(perm.student_id, f"Your {perm.perm_type} request was rejected by HOD. Remarks: {remarks}", "danger")
        flash('Request rejected.', 'warning')

    db.session.commit()
    return redirect(url_for('hod_approvals'))


@app.route('/hod/bonafides')
@login_required(role='hod')
def hod_bonafides():
    user = get_current_user()
    bonafides = Bonafide.query.join(User, Bonafide.student_id == User.id).filter(User.dept_id == user.dept_id).order_by(Bonafide.created_at.desc()).all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('hod/bonafides.html', user=user, bonafides=bonafides, notif_count=notifs)


@app.route('/hod/bonafide/approve/<int:bon_id>', methods=['POST'])
@login_required(role='hod')
def hod_approve_bonafide(bon_id):
    user = get_current_user()
    bon = db.get_or_404(Bonafide, bon_id)
    action = request.form.get('action')
    bon.remarks = request.form.get('remarks', '')
    bon.approved_by = user.id
    if action == 'approve':
        bon.status = 'approved'
        add_notification(bon.student_id, "Your bonafide certificate has been approved by HOD!", "success")
        flash('Bonafide approved!', 'success')
    else:
        bon.status = 'rejected'
        add_notification(bon.student_id, f"Your bonafide request was rejected. Remarks: {bon.remarks}", "danger")
        flash('Bonafide rejected.', 'warning')
    db.session.commit()
    return redirect(url_for('hod_bonafides'))


@app.route('/hod/reports')
@login_required(role='hod')
def hod_reports():
    user = get_current_user()
    dept_students = User.query.filter_by(dept_id=user.dept_id, role='student').all()
    student_ids = [s.id for s in dept_students]
    total = Permission.query.filter(Permission.student_id.in_(student_ids)).count()
    approved = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'approved').count()
    rejected = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'rejected').count()
    pending = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.status == 'pending').count()
    forwarded = Permission.query.filter(Permission.student_id.in_(student_ids), Permission.forwarded_to_hod == True).count()
    staff_list = User.query.filter_by(dept_id=user.dept_id, role='staff').all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('hod/reports.html', user=user, total=total, approved=approved,
                           rejected=rejected, pending=pending, forwarded=forwarded,
                           staff_list=staff_list, students=dept_students, notif_count=notifs)


# ─── Admin Routes ─────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    user = get_current_user()
    total_students = User.query.filter_by(role='student').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_depts = Department.query.count()
    active_requests = Permission.query.filter(Permission.status.in_(['pending', 'forwarded'])).count()
    total_requests = Permission.query.count()
    approved = Permission.query.filter_by(status='approved').count()
    rejected = Permission.query.filter_by(status='rejected').count()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('admin/dashboard.html', user=user, total_students=total_students,
                           total_staff=total_staff, total_depts=total_depts,
                           active_requests=active_requests, total_requests=total_requests,
                           approved=approved, rejected=rejected, notif_count=notifs)


@app.route('/admin/students', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_students():
    user = get_current_user()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Check for duplicate reg_no
            if User.query.filter_by(reg_no=request.form['reg_no']).first():
                flash(f"Register number {request.form['reg_no']} already exists!", 'danger')
                return redirect(url_for('admin_students'))
            s = User(
                name=request.form['name'], reg_no=request.form['reg_no'],
                email=request.form.get('email') or None, role='student',
                dept_id=int(request.form['dept_id']),
                year=int(request.form['year']), section=request.form['section'],
                phone=request.form.get('phone')
            )
            s.set_password(request.form.get('password', 'student123'))
            db.session.add(s)
            try:
                db.session.commit()
                flash(f'Student {s.name} added successfully!', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('Failed to add student. Email or register number may already exist.', 'danger')
        elif action == 'delete':
            u = db.session.get(User, int(request.form['user_id']))
            if u:
                u.is_active = False
                db.session.commit()
                flash('Student deactivated.', 'warning')
        elif action == 'toggle':
            u = db.session.get(User, int(request.form['user_id']))
            if u:
                u.is_active = not u.is_active
                db.session.commit()
                flash(f"Student {'activated' if u.is_active else 'deactivated'}.", 'info')
        return redirect(url_for('admin_students'))
    students = User.query.filter_by(role='student').order_by(User.name).all()
    departments = Department.query.all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('admin/students.html', user=user, students=students,
                           departments=departments, notif_count=notifs)


@app.route('/admin/staff', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_staff():
    user = get_current_user()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Check for duplicate email
            if request.form.get('email') and User.query.filter_by(email=request.form['email']).first():
                flash(f"Email {request.form['email']} already exists!", 'danger')
                return redirect(url_for('admin_staff'))
            s = User(
                name=request.form['name'], email=request.form.get('email') or None,
                role=request.form['staff_role'],
                dept_id=int(request.form['dept_id']),
                designation=request.form.get('designation'),
                phone=request.form.get('phone')
            )
            s.set_password(request.form.get('password', 'staff123'))
            db.session.add(s)
            try:
                db.session.commit()
                flash(f'{s.role.upper()} {s.name} added successfully!', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('Failed to add staff. Email may already be in use.', 'danger')
        elif action == 'toggle':
            u = db.session.get(User, int(request.form['user_id']))
            if u:
                u.is_active = not u.is_active
                db.session.commit()
        return redirect(url_for('admin_staff'))
    staff_list = User.query.filter(User.role.in_(['staff', 'hod'])).order_by(User.role, User.name).all()
    departments = Department.query.all()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('admin/staff.html', user=user, staff_list=staff_list,
                           departments=departments, notif_count=notifs)


@app.route('/admin/departments', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_departments():
    user = get_current_user()
    if request.method == 'POST':
        d = Department(name=request.form['name'], code=request.form['code'])
        db.session.add(d)
        db.session.commit()
        flash('Department added!', 'success')
        return redirect(url_for('admin_departments'))
    departments = Department.query.all()
    dept_stats = []
    for d in departments:
        studs = User.query.filter_by(dept_id=d.id, role='student').count()
        staff = User.query.filter_by(dept_id=d.id, role='staff').count()
        dept_stats.append({'dept': d, 'students': studs, 'staff': staff})
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('admin/departments.html', user=user, dept_stats=dept_stats, notif_count=notifs)


@app.route('/admin/reports')
@login_required(role='admin')
def admin_reports():
    user = get_current_user()
    departments = Department.query.all()
    dept_data = []
    for d in departments:
        studs = User.query.filter_by(dept_id=d.id, role='student').all()
        sids = [s.id for s in studs]
        total = Permission.query.filter(Permission.student_id.in_(sids)).count()
        dept_data.append({'name': d.name, 'code': d.code, 'students': len(studs), 'requests': total})
    total_perm = Permission.query.count()
    approved = Permission.query.filter_by(status='approved').count()
    rejected = Permission.query.filter_by(status='rejected').count()
    pending = Permission.query.filter_by(status='pending').count()
    forwarded = Permission.query.filter_by(status='forwarded').count()
    notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return render_template('admin/reports.html', user=user, dept_data=dept_data,
                           total_perm=total_perm, approved=approved, rejected=rejected,
                           pending=pending, forwarded=forwarded, notif_count=notifs)


# ─── Gate Pass Route ──────────────────────────────────────────────────────────

@app.route('/gate_pass/<int:perm_id>')
def gate_pass(perm_id):
    perm = db.get_or_404(Permission, perm_id)
    student = perm.student
    staff = perm.staff
    return render_template('gate_pass.html', perm=perm, student=student, staff=staff)


# ─── API: Mark notifications read ────────────────────────────────────────────

@app.route('/notifications/mark_read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})


# ─── Public Verification Route ────────────────────────────────────────────────
@app.route('/verify/<int:perm_id>')
def verify_pass(perm_id):
    perm = db.get_or_404(Permission, perm_id)
    # The view does not require a login, it is public for scanning by guards
    return render_template('verify_pass.html', perm=perm)


# ─── QR Scanner Route ─────────────────────────────────────────────────────────
@app.route('/scan')
def qr_scanner():
    """Public page that lets guards scan a gate pass QR code with their camera."""
    return render_template('qr_scanner.html')


if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

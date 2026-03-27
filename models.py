from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)

    students = db.relationship('User', foreign_keys='User.dept_id', backref='department', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    reg_no = db.Column(db.String(50), unique=True, nullable=True)  # For students
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, staff, hod, admin
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    photo = db.Column(db.String(200), nullable=True, default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Student specific
    year = db.Column(db.Integer, nullable=True)
    section = db.Column(db.String(5), nullable=True)

    # Staff specific
    designation = db.Column(db.String(100), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def display_id(self):
        return self.reg_no if self.reg_no else self.email


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    perm_type = db.Column(db.String(20), nullable=False)  # leave, outing
    from_date = db.Column(db.String(20), nullable=False)
    to_date = db.Column(db.String(20), nullable=False)
    from_time = db.Column(db.String(10), nullable=True)
    to_time = db.Column(db.String(10), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, forwarded
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    staff_remarks = db.Column(db.Text, nullable=True)
    hod_remarks = db.Column(db.Text, nullable=True)
    forwarded_to_hod = db.Column(db.Boolean, default=False)
    qr_code_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id], backref='permissions')
    staff = db.relationship('User', foreign_keys=[staff_id], backref='reviewed_permissions')


class Bonafide(db.Model):
    __tablename__ = 'bonafides'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    remarks = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id], backref='bonafides')
    approver = db.relationship('User', foreign_keys=[approved_by])


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    total_classes = db.Column(db.Integer, default=0)
    attended_classes = db.Column(db.Integer, default=0)

    student = db.relationship('User', foreign_keys=[student_id], backref='attendance')

    @property
    def percentage(self):
        if self.total_classes == 0:
            return 0
        return round((self.attended_classes / self.total_classes) * 100, 1)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notif_type = db.Column(db.String(30), default='info')  # info, success, warning, danger
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')

from app import create_app
from models import db, Department, User, Permission, Bonafide, Attendance, Notification
from gate_pass import generate_gate_pass_qr
from datetime import datetime, timedelta

def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Departments
        cs = Department(name="Computer Science & Engineering", code="CSE")
        ec = Department(name="Electronics & Communication Engineering", code="ECE")
        db.session.add_all([cs, ec])
        db.session.commit()

        # Admin
        admin = User(name="System Administrator", email="admin@college.edu", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # HOD
        hod = User(name="Dr. Ramesh Kumar", email="hod@college.edu", role="hod",
                   dept_id=cs.id, designation="Head of Department")
        hod.set_password("hod123")
        db.session.add(hod)

        hod2 = User(name="Dr. Priya Nair", email="hod.ece@college.edu", role="hod",
                    dept_id=ec.id, designation="Head of Department")
        hod2.set_password("hod123")
        db.session.add(hod2)

        # Staff
        staff = User(name="Prof. Anitha Selvan", email="staff@college.edu", role="staff",
                     dept_id=cs.id, designation="Class Advisor – III CSE A")
        staff.set_password("staff123")
        db.session.add(staff)

        staff2 = User(name="Prof. Karthik Rajan", email="staff2@college.edu", role="staff",
                      dept_id=cs.id, designation="Class Advisor – II CSE B")
        staff2.set_password("staff123")
        db.session.add(staff2)

        # Students
        students_data = [
            ("Naveen Kumar S", "22CS001", cs.id, 3, "A"),
            ("Priya Dharshini R", "22CS002", cs.id, 3, "A"),
            ("Arjun Balaji", "22CS003", cs.id, 3, "A"),
            ("Divya Menon", "22CS004", cs.id, 3, "B"),
            ("Rahul Sharma", "21CS005", cs.id, 4, "A"),
        ]
        student_objs = []
        for idx, (name, reg, dept, year, sec) in enumerate(students_data):
            u = User(name=name, reg_no=reg, email=f"{reg.lower()}@student.edu",
                     role="student", dept_id=dept, year=year, section=sec)
            u.set_password("student123")
            db.session.add(u)
            student_objs.append(u)
        db.session.commit()

        # Permissions
        today = datetime.now()
        perms_data = [
            (student_objs[0], "outing", (today - timedelta(days=5)).strftime("%Y-%m-%d"),
             (today - timedelta(days=5)).strftime("%Y-%m-%d"), "Family function", "approved", staff.id, "Approved", None, False),
            (student_objs[0], "leave", (today - timedelta(days=2)).strftime("%Y-%m-%d"),
             (today - timedelta(days=1)).strftime("%Y-%m-%d"), "Fever - medical leave", "pending", None, None, None, False),
            (student_objs[1], "outing", today.strftime("%Y-%m-%d"),
             today.strftime("%Y-%m-%d"), "Bank work", "forwarded", staff.id, "Forwarded to HOD for review", None, True),
            (student_objs[2], "leave", (today - timedelta(days=10)).strftime("%Y-%m-%d"),
             (today - timedelta(days=8)).strftime("%Y-%m-%d"), "Out of station", "rejected", staff.id, "Insufficient reason", None, False),
            (student_objs[3], "outing", (today + timedelta(days=1)).strftime("%Y-%m-%d"),
             (today + timedelta(days=1)).strftime("%Y-%m-%d"), "Dental appointment", "pending", None, None, None, False),
        ]

        perm_objs = []
        for (stu, ptype, fd, td, reason, status, sid, sremark, hremark, forwarded) in perms_data:
            p = Permission(student_id=stu.id, perm_type=ptype, from_date=fd, to_date=td,
                           reason=reason, status=status, staff_id=sid,
                           staff_remarks=sremark, hod_remarks=hremark,
                           forwarded_to_hod=forwarded)
            db.session.add(p)
            perm_objs.append(p)
        db.session.commit()

        # Generate QR for the already-approved demo permission
        approved_perm = perm_objs[0]
        approved_perm.qr_code_path = generate_gate_pass_qr(approved_perm, approved_perm.student, staff.name)
        db.session.commit()

        # Bonafides
        b1 = Bonafide(student_id=student_objs[0].id, purpose="For bank account opening", status="approved", approved_by=hod.id)
        b2 = Bonafide(student_id=student_objs[1].id, purpose="For passport application", status="pending")
        b3 = Bonafide(student_id=student_objs[2].id, purpose="For scholarship application", status="pending")
        db.session.add_all([b1, b2, b3])

        # Attendance
        subjects = [
            ("Data Structures & Algorithms", 60, 55),
            ("Database Management Systems", 55, 48),
            ("Operating Systems", 50, 42),
            ("Computer Networks", 58, 52),
            ("Software Engineering", 45, 40),
        ]
        for stu in student_objs:
            for subj, total, attended in subjects:
                a = Attendance(student_id=stu.id, subject=subj,
                               total_classes=total,
                               attended_classes=max(0, attended - (student_objs.index(stu) * 2)))
                db.session.add(a)

        # Notifications
        notifs = [
            (student_objs[0].id, "Your outing request has been approved!", "success"),
            (student_objs[0].id, "Your bonafide certificate is ready for download.", "info"),
            (student_objs[1].id, "Your permission request has been forwarded to HOD.", "warning"),
            (student_objs[2].id, "Your leave request was rejected. Please check remarks.", "danger"),
        ]
        for uid, msg, ntype in notifs:
            db.session.add(Notification(user_id=uid, message=msg, notif_type=ntype))

        db.session.commit()
        print("✅ Database seeded successfully!")
        print("\nDemo Credentials:")
        print("  Student : 22CS001 / student123")
        print("  Staff   : staff@college.edu / staff123")
        print("  HOD     : hod@college.edu / hod123")
        print("  Admin   : admin@college.edu / admin123")

if __name__ == "__main__":
    seed()

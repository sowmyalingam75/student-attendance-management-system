import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from werkzeug.security import generate_password_hash
from routes.auth import login_required
from utils.database import query_db, modify_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required('admin')
def require_admin():
    pass


# -------------------------------------------------------------------------
# Admin Dashboard
# -------------------------------------------------------------------------
@admin_bp.route('/dashboard')
def dashboard():
    # Key counts
    total_students = query_db("SELECT COUNT(*) as cnt FROM students", one=True)['cnt']
    total_teachers = query_db("SELECT COUNT(*) as cnt FROM teachers", one=True)['cnt']
    total_subjects = query_db("SELECT COUNT(*) as cnt FROM subjects", one=True)['cnt']
    
    # Today's attendance stats
    today_present = query_db(
        "SELECT COUNT(*) as cnt FROM attendance WHERE attendance_date = CURDATE() AND status = 'Present'", 
        one=True
    )['cnt']
    today_absent = query_db(
        "SELECT COUNT(*) as cnt FROM attendance WHERE attendance_date = CURDATE() AND status = 'Absent'", 
        one=True
    )['cnt']
    
    # If no attendance marked today, fetch statistics from the most recent date with records for preview
    if today_present == 0 and today_absent == 0:
        latest_date_row = query_db("SELECT MAX(attendance_date) as max_date FROM attendance", one=True)
        if latest_date_row and latest_date_row['max_date']:
            latest_date = latest_date_row['max_date']
            today_present = query_db(
                "SELECT COUNT(*) as cnt FROM attendance WHERE attendance_date = %s AND status = 'Present'", 
                (latest_date,), one=True
            )['cnt']
            today_absent = query_db(
                "SELECT COUNT(*) as cnt FROM attendance WHERE attendance_date = %s AND status = 'Absent'", 
                (latest_date,), one=True
            )['cnt']
            date_label = f"Latest ({latest_date})"
        else:
            date_label = "Today"
    else:
        date_label = "Today"

    # Overall Attendance totals
    overall_stats = query_db("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as total_present,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as total_absent
        FROM attendance
    """, one=True)
    
    tot_rec = overall_stats['total_records'] or 0
    tot_pres = overall_stats['total_present'] or 0
    tot_abs = overall_stats['total_absent'] or 0
    overall_pct = round((tot_pres / tot_rec * 100), 1) if tot_rec > 0 else 0.0

    # Trend data: Daily attendance for the last 7 distinct dates
    trend_rows = query_db("""
        SELECT attendance_date,
               SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_cnt,
               SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_cnt
        FROM attendance
        GROUP BY attendance_date
        ORDER BY attendance_date ASC
        LIMIT 10
    """)
    trend_labels = [str(r['attendance_date']) for r in trend_rows]
    trend_present = [r['present_cnt'] for r in trend_rows]
    trend_absent = [r['absent_cnt'] for r in trend_rows]

    # Subject-wise attendance distribution
    subject_stats = query_db("""
        SELECT s.subject_name, s.subject_code,
               COUNT(a.id) as total_sessions,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_cnt
        FROM subjects s
        LEFT JOIN attendance a ON s.id = a.subject_id
        GROUP BY s.id, s.subject_name, s.subject_code
    """)
    subject_labels = [f"{s['subject_code']}" for s in subject_stats]
    subject_percentages = [
        round((s['present_cnt'] / s['total_sessions'] * 100), 1) if s['total_sessions'] and s['total_sessions'] > 0 else 0
        for s in subject_stats
    ]

    # Recent attendance logs (last 8)
    recent_logs = query_db("""
        SELECT a.id, a.attendance_date, a.status, st.student_id, st.name as student_name,
               sub.subject_name, sub.subject_code, t.name as teacher_name
        FROM attendance a
        JOIN students st ON a.student_id = st.id
        JOIN subjects sub ON a.subject_id = sub.id
        JOIN teachers t ON a.teacher_id = t.id
        ORDER BY a.attendance_date DESC, a.id DESC
        LIMIT 8
    """)

    # Count of low-attendance students (< 75%)
    low_att_count = query_db("""
        SELECT COUNT(*) as cnt FROM (
            SELECT student_id,
                   (SUM(CASE WHEN status = 'Present' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100 as pct
            FROM attendance
            GROUP BY student_id
            HAVING pct < 75
        ) as subq
    """, one=True)['cnt']

    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_subjects=total_subjects,
        today_present=today_present,
        today_absent=today_absent,
        date_label=date_label,
        overall_pct=overall_pct,
        tot_pres=tot_pres,
        tot_abs=tot_abs,
        low_att_count=low_att_count,
        recent_logs=recent_logs,
        trend_labels=trend_labels,
        trend_present=trend_present,
        trend_absent=trend_absent,
        subject_labels=subject_labels,
        subject_percentages=subject_percentages
    )


# -------------------------------------------------------------------------
# Student Management CRUD
# -------------------------------------------------------------------------
@admin_bp.route('/students')
def students():
    student_list = query_db("""
        SELECT s.*,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended_classes
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        ORDER BY s.student_id ASC
    """)
    for s in student_list:
        tot = s['total_classes'] or 0
        att = s['attended_classes'] or 0
        s['percentage'] = round((att / tot * 100), 1) if tot > 0 else 0.0
    return render_template('admin/students.html', students=student_list)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        section = request.form.get('section', '').strip()
        password = request.form.get('password', '').strip()

        # Validation
        if not (student_id and name and email and department and year and section and password):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_student.html', form=request.form)

        # Check unique student_id and email
        existing_sid = query_db("SELECT id FROM students WHERE student_id = %s", (student_id,), one=True)
        if existing_sid:
            flash(f"Student ID '{student_id}' already exists. Please choose a unique Student ID.", 'danger')
            return render_template('admin/add_student.html', form=request.form)

        existing_user = query_db("SELECT id FROM users WHERE username = %s", (student_id,), one=True)
        if existing_user:
            flash(f"Username '{student_id}' is already registered.", 'danger')
            return render_template('admin/add_student.html', form=request.form)

        hashed_pass = generate_password_hash(password)

        try:
            # Insert into students table
            modify_db("""
                INSERT INTO students (student_id, name, email, phone, department, year, section, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (student_id, name, email, phone, department, year, section, hashed_pass))

            # Insert into users table
            modify_db("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, 'student')
            """, (student_id, hashed_pass))

            flash(f"Student '{name}' ({student_id}) added successfully!", 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            flash(f"Error adding student: {e}", 'danger')
            return render_template('admin/add_student.html', form=request.form)

    return render_template('admin/add_student.html')


@admin_bp.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = query_db("SELECT * FROM students WHERE id = %s", (id,), one=True)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        section = request.form.get('section', '').strip()
        new_password = request.form.get('password', '').strip()

        if not (name and email and department and year and section):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/edit_student.html', student=student)

        try:
            if new_password:
                hashed_pass = generate_password_hash(new_password)
                modify_db("""
                    UPDATE students 
                    SET name=%s, email=%s, phone=%s, department=%s, year=%s, section=%s, password=%s
                    WHERE id=%s
                """, (name, email, phone, department, year, section, hashed_pass, id))

                modify_db("UPDATE users SET password=%s WHERE username=%s", (hashed_pass, student['student_id']))
            else:
                modify_db("""
                    UPDATE students 
                    SET name=%s, email=%s, phone=%s, department=%s, year=%s, section=%s
                    WHERE id=%s
                """, (name, email, phone, department, year, section, id))

            flash(f"Student '{name}' updated successfully!", 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            flash(f"Error updating student: {e}", 'danger')
            return render_template('admin/edit_student.html', student=student)

    return render_template('admin/edit_student.html', student=student)


@admin_bp.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    student = query_db("SELECT * FROM students WHERE id = %s", (id,), one=True)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))

    try:
        sid = student['student_id']
        modify_db("DELETE FROM students WHERE id = %s", (id,))
        modify_db("DELETE FROM users WHERE username = %s", (sid,))
        flash(f"Student '{student['name']}' ({sid}) deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting student: {e}", 'danger')

    return redirect(url_for('admin.students'))


# -------------------------------------------------------------------------
# Teacher Management CRUD
# -------------------------------------------------------------------------
@admin_bp.route('/teachers')
def teachers():
    teacher_list = query_db("""
        SELECT t.*, 
               COUNT(ts.id) as assigned_subjects_count,
               GROUP_CONCAT(sub.subject_code SEPARATOR ', ') as assigned_subjects
        FROM teachers t
        LEFT JOIN teacher_subjects ts ON t.id = ts.teacher_id
        LEFT JOIN subjects sub ON ts.subject_id = sub.id
        GROUP BY t.id
        ORDER BY t.teacher_id ASC
    """)
    return render_template('admin/teachers.html', teachers=teacher_list)


@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '').strip()

        if not (teacher_id and name and email and department and password):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_teacher.html', form=request.form)

        existing_tid = query_db("SELECT id FROM teachers WHERE teacher_id = %s", (teacher_id,), one=True)
        if existing_tid:
            flash(f"Teacher ID '{teacher_id}' already exists.", 'danger')
            return render_template('admin/add_teacher.html', form=request.form)

        existing_user = query_db("SELECT id FROM users WHERE username = %s", (teacher_id,), one=True)
        if existing_user:
            flash(f"Username '{teacher_id}' is already registered.", 'danger')
            return render_template('admin/add_teacher.html', form=request.form)

        hashed_pass = generate_password_hash(password)

        try:
            modify_db("""
                INSERT INTO teachers (teacher_id, name, email, phone, department, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (teacher_id, name, email, phone, department, hashed_pass))

            modify_db("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, 'teacher')
            """, (teacher_id, hashed_pass))

            flash(f"Teacher '{name}' added successfully!", 'success')
            return redirect(url_for('admin.teachers'))
        except Exception as e:
            flash(f"Error adding teacher: {e}", 'danger')
            return render_template('admin/add_teacher.html', form=request.form)

    return render_template('admin/add_teacher.html')


@admin_bp.route('/teachers/edit/<int:id>', methods=['GET', 'POST'])
def edit_teacher(id):
    teacher = query_db("SELECT * FROM teachers WHERE id = %s", (id,), one=True)
    if not teacher:
        flash('Teacher not found.', 'danger')
        return redirect(url_for('admin.teachers'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        new_password = request.form.get('password', '').strip()

        if not (name and email and department):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/edit_teacher.html', teacher=teacher)

        try:
            if new_password:
                hashed_pass = generate_password_hash(new_password)
                modify_db("""
                    UPDATE teachers 
                    SET name=%s, email=%s, phone=%s, department=%s, password=%s
                    WHERE id=%s
                """, (name, email, phone, department, hashed_pass, id))
                modify_db("UPDATE users SET password=%s WHERE username=%s", (hashed_pass, teacher['teacher_id']))
            else:
                modify_db("""
                    UPDATE teachers 
                    SET name=%s, email=%s, phone=%s, department=%s
                    WHERE id=%s
                """, (name, email, phone, department, id))

            flash(f"Teacher '{name}' updated successfully!", 'success')
            return redirect(url_for('admin.teachers'))
        except Exception as e:
            flash(f"Error updating teacher: {e}", 'danger')
            return render_template('admin/edit_teacher.html', teacher=teacher)

    return render_template('admin/edit_teacher.html', teacher=teacher)


@admin_bp.route('/teachers/delete/<int:id>', methods=['POST'])
def delete_teacher(id):
    teacher = query_db("SELECT * FROM teachers WHERE id = %s", (id,), one=True)
    if not teacher:
        flash('Teacher not found.', 'danger')
        return redirect(url_for('admin.teachers'))

    try:
        tid = teacher['teacher_id']
        modify_db("DELETE FROM teachers WHERE id = %s", (id,))
        modify_db("DELETE FROM users WHERE username = %s", (tid,))
        flash(f"Teacher '{teacher['name']}' deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting teacher: {e}", 'danger')

    return redirect(url_for('admin.teachers'))


# -------------------------------------------------------------------------
# Subject Management CRUD
# -------------------------------------------------------------------------
@admin_bp.route('/subjects')
def subjects():
    subject_list = query_db("""
        SELECT s.*, 
               GROUP_CONCAT(t.name SEPARATOR ', ') as assigned_teachers
        FROM subjects s
        LEFT JOIN teacher_subjects ts ON s.id = ts.subject_id
        LEFT JOIN teachers t ON ts.teacher_id = t.id
        GROUP BY s.id
        ORDER BY s.subject_code ASC
    """)
    return render_template('admin/subjects.html', subjects=subject_list)


@admin_bp.route('/subjects/add', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_code = request.form.get('subject_code', '').strip().upper()
        subject_name = request.form.get('subject_name', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        section = request.form.get('section', '').strip()

        if not (subject_code and subject_name and department and year and section):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_subject.html', form=request.form)

        existing_sub = query_db("SELECT id FROM subjects WHERE subject_code = %s", (subject_code,), one=True)
        if existing_sub:
            flash(f"Subject Code '{subject_code}' already exists.", 'danger')
            return render_template('admin/add_subject.html', form=request.form)

        try:
            modify_db("""
                INSERT INTO subjects (subject_code, subject_name, department, year, section)
                VALUES (%s, %s, %s, %s, %s)
            """, (subject_code, subject_name, department, year, section))
            flash(f"Subject '{subject_name}' ({subject_code}) added successfully!", 'success')
            return redirect(url_for('admin.subjects'))
        except Exception as e:
            flash(f"Error adding subject: {e}", 'danger')
            return render_template('admin/add_subject.html', form=request.form)

    return render_template('admin/add_subject.html')


@admin_bp.route('/subjects/edit/<int:id>', methods=['GET', 'POST'])
def edit_subject(id):
    subject = query_db("SELECT * FROM subjects WHERE id = %s", (id,), one=True)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin.subjects'))

    if request.method == 'POST':
        subject_name = request.form.get('subject_name', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        section = request.form.get('section', '').strip()

        if not (subject_name and department and year and section):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/edit_subject.html', subject=subject)

        try:
            modify_db("""
                UPDATE subjects
                SET subject_name=%s, department=%s, year=%s, section=%s
                WHERE id=%s
            """, (subject_name, department, year, section, id))
            flash(f"Subject '{subject_name}' updated successfully!", 'success')
            return redirect(url_for('admin.subjects'))
        except Exception as e:
            flash(f"Error updating subject: {e}", 'danger')
            return render_template('admin/edit_subject.html', subject=subject)

    return render_template('admin/edit_subject.html', subject=subject)


@admin_bp.route('/subjects/delete/<int:id>', methods=['POST'])
def delete_subject(id):
    subject = query_db("SELECT * FROM subjects WHERE id = %s", (id,), one=True)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin.subjects'))

    try:
        modify_db("DELETE FROM subjects WHERE id = %s", (id,))
        flash(f"Subject '{subject['subject_name']}' deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting subject: {e}", 'danger')

    return redirect(url_for('admin.subjects'))


# -------------------------------------------------------------------------
# Teacher-Subject Assignment
# -------------------------------------------------------------------------
@admin_bp.route('/assign-subject', methods=['GET', 'POST'])
def assign_subject():
    teachers_list = query_db("SELECT id, teacher_id, name, department FROM teachers ORDER BY name ASC")
    subjects_list = query_db("SELECT id, subject_code, subject_name, department, year, section FROM subjects ORDER BY subject_code ASC")

    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        subject_id = request.form.get('subject_id')

        if not (teacher_id and subject_id):
            flash('Please select both a teacher and a subject.', 'warning')
            return redirect(url_for('admin.assign_subject'))

        # Check existing assignment
        existing = query_db(
            "SELECT id FROM teacher_subjects WHERE teacher_id = %s AND subject_id = %s",
            (teacher_id, subject_id),
            one=True
        )
        if existing:
            flash('This subject is already assigned to the selected teacher.', 'warning')
            return redirect(url_for('admin.assign_subject'))

        try:
            modify_db(
                "INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (%s, %s)",
                (teacher_id, subject_id)
            )
            flash('Subject assigned to teacher successfully!', 'success')
            return redirect(url_for('admin.assign_subject'))
        except Exception as e:
            flash(f"Error assigning subject: {e}", 'danger')

    assignments = query_db("""
        SELECT ts.id, t.name as teacher_name, t.teacher_id,
               sub.subject_code, sub.subject_name, sub.department, sub.year, sub.section
        FROM teacher_subjects ts
        JOIN teachers t ON ts.teacher_id = t.id
        JOIN subjects sub ON ts.subject_id = sub.id
        ORDER BY t.name ASC, sub.subject_code ASC
    """)

    return render_template('admin/assign_subject.html',
        teachers=teachers_list,
        subjects=subjects_list,
        assignments=assignments
    )


@admin_bp.route('/unassign-subject/<int:id>', methods=['POST'])
def unassign_subject(id):
    try:
        modify_db("DELETE FROM teacher_subjects WHERE id = %s", (id,))
        flash('Subject assignment removed successfully.', 'success')
    except Exception as e:
        flash(f"Error removing assignment: {e}", 'danger')
    return redirect(url_for('admin.assign_subject'))


# -------------------------------------------------------------------------
# Attendance View
# -------------------------------------------------------------------------
@admin_bp.route('/attendance')
def attendance():
    subjects_list = query_db("SELECT id, subject_code, subject_name FROM subjects ORDER BY subject_code ASC")
    subject_id = request.args.get('subject_id')
    date_filter = request.args.get('date')
    status_filter = request.args.get('status')

    query = """
        SELECT a.id, a.attendance_date, a.status,
               s.student_id, s.name as student_name, s.department, s.year, s.section,
               sub.subject_code, sub.subject_name,
               t.name as teacher_name
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN subjects sub ON a.subject_id = sub.id
        JOIN teachers t ON a.teacher_id = t.id
        WHERE 1=1
    """
    params = []

    if subject_id:
        query += " AND a.subject_id = %s"
        params.append(subject_id)
    if date_filter:
        query += " AND a.attendance_date = %s"
        params.append(date_filter)
    if status_filter:
        query += " AND a.status = %s"
        params.append(status_filter)

    query += " ORDER BY a.attendance_date DESC, sub.subject_code ASC, s.student_id ASC LIMIT 200"

    records = query_db(query, tuple(params))
    return render_template('admin/attendance.html',
        records=records,
        subjects=subjects_list,
        selected_subject=subject_id,
        selected_date=date_filter,
        selected_status=status_filter
    )


# -------------------------------------------------------------------------
# Attendance Reports & CSV Export
# -------------------------------------------------------------------------
@admin_bp.route('/reports')
def reports():
    subjects_list = query_db("SELECT id, subject_code, subject_name FROM subjects ORDER BY subject_code ASC")
    subject_id = request.args.get('subject_id')

    query = """
        SELECT s.student_id, s.name as student_name, s.department, s.year, s.section,
               sub.id as subject_id, sub.subject_code, sub.subject_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM students s
        CROSS JOIN subjects sub
        LEFT JOIN attendance a ON s.id = a.student_id AND sub.id = a.subject_id
        WHERE 1=1
    """
    params = []
    if subject_id:
        query += " AND sub.id = %s"
        params.append(subject_id)

    query += " GROUP BY s.id, sub.id HAVING total_classes > 0 ORDER BY s.student_id ASC, sub.subject_code ASC"
    
    report_data = query_db(query, tuple(params))
    for row in report_data:
        tot = row['total_classes'] or 0
        pres = row['present_count'] or 0
        pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
        row['percentage'] = pct
        if pct >= 75:
            row['badge_class'] = 'badge-success'
            row['status_text'] = 'Good Attendance'
        elif pct >= 65:
            row['badge_class'] = 'badge-warning'
            row['status_text'] = 'Low Attendance'
        else:
            row['badge_class'] = 'badge-danger'
            row['status_text'] = 'Critical Attendance'

    return render_template('admin/reports.html',
        reports=report_data,
        subjects=subjects_list,
        selected_subject=subject_id
    )


@admin_bp.route('/export-csv')
def export_csv():
    subject_id = request.args.get('subject_id')

    query = """
        SELECT s.student_id, s.name as student_name, s.department, s.year, s.section,
               sub.subject_code, sub.subject_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM students s
        CROSS JOIN subjects sub
        LEFT JOIN attendance a ON s.id = a.student_id AND sub.id = a.subject_id
        WHERE 1=1
    """
    params = []
    if subject_id:
        query += " AND sub.id = %s"
        params.append(subject_id)

    query += " GROUP BY s.id, sub.id HAVING total_classes > 0 ORDER BY s.student_id ASC, sub.subject_code ASC"
    rows = query_db(query, tuple(params))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Student Name', 'Department', 'Year', 'Section', 'Subject Code', 'Subject Name', 'Total Classes', 'Present', 'Absent', 'Percentage', 'Status'])

    for r in rows:
        tot = r['total_classes'] or 0
        pres = r['present_count'] or 0
        absent = r['absent_count'] or 0
        pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
        status = 'Good Attendance' if pct >= 75 else ('Low Attendance' if pct >= 65 else 'Critical Attendance')
        writer.writerow([
            r['student_id'], r['student_name'], r['department'], r['year'], r['section'],
            r['subject_code'], r['subject_name'], tot, pres, absent, f"{pct}%", status
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=attendance_report.csv"}
    )


# -------------------------------------------------------------------------
# Low Attendance Students Page (< 75%)
# -------------------------------------------------------------------------
@admin_bp.route('/low-attendance')
def low_attendance():
    low_records = query_db("""
        SELECT s.student_id, s.name as student_name, s.department, s.year, s.section,
               sub.subject_code, sub.subject_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM students s
        CROSS JOIN subjects sub
        LEFT JOIN attendance a ON s.id = a.student_id AND sub.id = a.subject_id
        GROUP BY s.id, sub.id
        HAVING total_classes > 0 AND (present_count * 100.0 / total_classes) < 75.0
        ORDER BY (present_count * 100.0 / total_classes) ASC, s.student_id ASC
    """)

    for r in low_records:
        tot = r['total_classes']
        pres = r['present_count']
        pct = round((pres / tot * 100), 1)
        r['percentage'] = pct
        if pct < 65:
            r['badge_class'] = 'badge-danger'
            r['status_text'] = 'Critical Attendance (<65%)'
        else:
            r['badge_class'] = 'badge-warning'
            r['status_text'] = 'Low Attendance (<75%)'

    return render_template('admin/low_attendance.html', records=low_records)

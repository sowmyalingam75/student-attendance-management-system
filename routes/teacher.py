import io
import csv
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from routes.auth import login_required
from utils.database import query_db, modify_db

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.before_request
@login_required('teacher')
def require_teacher():
    pass


def get_current_teacher():
    """Helper to get current logged-in teacher info."""
    tid = session.get('username')
    return query_db("SELECT * FROM teachers WHERE teacher_id = %s", (tid,), one=True)


# -------------------------------------------------------------------------
# Teacher Dashboard
# -------------------------------------------------------------------------
@teacher_bp.route('/dashboard')
def dashboard():
    teacher = get_current_teacher()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    # Assigned subjects
    assigned_subjects = query_db("""
        SELECT s.*,
               COUNT(DISTINCT a.attendance_date) as total_sessions,
               (SELECT COUNT(*) FROM students st 
                WHERE st.department = s.department AND st.year = s.year AND st.section = s.section) as enrolled_students
        FROM teacher_subjects ts
        JOIN subjects s ON ts.subject_id = s.id
        LEFT JOIN attendance a ON s.id = a.subject_id AND a.teacher_id = %s
        WHERE ts.teacher_id = %s
        GROUP BY s.id
        ORDER BY s.subject_code ASC
    """, (teacher['id'], teacher['id']))

    # Total classes marked by this teacher
    total_marked_classes = query_db("""
        SELECT COUNT(DISTINCT CONCAT(subject_id, '_', attendance_date)) as cnt
        FROM attendance
        WHERE teacher_id = %s
    """, (teacher['id'],), one=True)['cnt']

    # Total unique students taught
    students_count = query_db("""
        SELECT COUNT(DISTINCT st.id) as cnt
        FROM students st
        JOIN subjects s ON st.department = s.department AND st.year = s.year AND st.section = s.section
        JOIN teacher_subjects ts ON s.id = ts.subject_id
        WHERE ts.teacher_id = %s
    """, (teacher['id'],), one=True)['cnt']

    # Recent attendance sessions
    recent_sessions = query_db("""
        SELECT a.attendance_date, sub.subject_code, sub.subject_name,
               COUNT(a.id) as total_students,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM attendance a
        JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.teacher_id = %s
        GROUP BY a.attendance_date, a.subject_id, sub.subject_code, sub.subject_name
        ORDER BY a.attendance_date DESC
        LIMIT 6
    """, (teacher['id'],))

    return render_template('teacher/dashboard.html',
        teacher=teacher,
        assigned_subjects=assigned_subjects,
        total_subjects=len(assigned_subjects),
        total_marked_classes=total_marked_classes,
        students_count=students_count,
        recent_sessions=recent_sessions
    )


# -------------------------------------------------------------------------
# Mark Attendance
# -------------------------------------------------------------------------
@teacher_bp.route('/mark-attendance', methods=['GET'])
def mark_attendance():
    teacher = get_current_teacher()
    assigned_subjects = query_db("""
        SELECT s.*
        FROM teacher_subjects ts
        JOIN subjects s ON ts.subject_id = s.id
        WHERE ts.teacher_id = %s
        ORDER BY s.subject_code ASC
    """, (teacher['id'],))

    selected_subject_id = request.args.get('subject_id', type=int)
    selected_date = request.args.get('date', date.today().isoformat())

    # Default to first subject if none selected
    if not selected_subject_id and assigned_subjects:
        selected_subject_id = assigned_subjects[0]['id']

    selected_subject = None
    students_list = []
    already_marked = False
    marked_summary = None

    if selected_subject_id:
        # Verify subject belongs to teacher
        selected_subject = query_db("""
            SELECT s.*
            FROM teacher_subjects ts
            JOIN subjects s ON ts.subject_id = s.id
            WHERE ts.teacher_id = %s AND s.id = %s
        """, (teacher['id'], selected_subject_id), one=True)

        if selected_subject:
            # Fetch all students for this department, year, section
            students_list = query_db("""
                SELECT s.id, s.student_id, s.name, s.department, s.year, s.section,
                       a.status as recorded_status, a.id as attendance_id
                FROM students s
                LEFT JOIN attendance a 
                    ON s.id = a.student_id 
                    AND a.subject_id = %s 
                    AND a.attendance_date = %s
                WHERE s.department = %s AND s.year = %s AND s.section = %s
                ORDER BY s.student_id ASC
            """, (
                selected_subject['id'],
                selected_date,
                selected_subject['department'],
                selected_subject['year'],
                selected_subject['section']
            ))

            # Check if any records are already marked
            existing_count = sum(1 for s in students_list if s['recorded_status'] is not None)
            if existing_count > 0:
                already_marked = True
                pres = sum(1 for s in students_list if s['recorded_status'] == 'Present')
                absn = sum(1 for s in students_list if s['recorded_status'] == 'Absent')
                marked_summary = {'present': pres, 'absent': absn, 'total': existing_count}

    return render_template('teacher/mark_attendance.html',
        assigned_subjects=assigned_subjects,
        selected_subject=selected_subject,
        selected_subject_id=selected_subject_id,
        selected_date=selected_date,
        students=students_list,
        already_marked=already_marked,
        marked_summary=marked_summary
    )


@teacher_bp.route('/save-attendance', methods=['POST'])
def save_attendance():
    teacher = get_current_teacher()
    subject_id = request.form.get('subject_id', type=int)
    attendance_date = request.form.get('attendance_date')

    if not subject_id or not attendance_date:
        flash('Subject and Date are required to record attendance.', 'danger')
        return redirect(url_for('teacher.mark_attendance'))

    # Verify authorization for subject
    authorized = query_db("""
        SELECT 1 FROM teacher_subjects 
        WHERE teacher_id = %s AND subject_id = %s
    """, (teacher['id'], subject_id), one=True)

    if not authorized:
        flash('You are not authorized to mark attendance for this subject.', 'danger')
        return redirect(url_for('teacher.mark_attendance'))

    # Subject info
    subject = query_db("SELECT * FROM subjects WHERE id = %s", (subject_id,), one=True)
    
    # Get students matching department, year, section
    students = query_db("""
        SELECT id FROM students
        WHERE department = %s AND year = %s AND section = %s
    """, (subject['department'], subject['year'], subject['section']))

    present_count = 0
    absent_count = 0

    try:
        for st in students:
            sid = st['id']
            status = request.form.get(f'status_{sid}', 'Absent')
            if status not in ('Present', 'Absent'):
                status = 'Absent'

            if status == 'Present':
                present_count += 1
            else:
                absent_count += 1

            # Check if record exists
            existing_record = query_db("""
                SELECT id FROM attendance 
                WHERE student_id = %s AND subject_id = %s AND attendance_date = %s
            """, (sid, subject_id, attendance_date), one=True)

            if existing_record:
                # Update existing
                modify_db("""
                    UPDATE attendance 
                    SET status = %s, teacher_id = %s
                    WHERE id = %s
                """, (status, teacher['id'], existing_record['id']))
            else:
                # Insert new
                modify_db("""
                    INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sid, subject_id, teacher['id'], attendance_date, status))

        flash(
            f"Attendance for '{subject['subject_name']}' on {attendance_date} saved successfully! "
            f"({present_count} Present, {absent_count} Absent)", 
            'success'
        )
    except Exception as e:
        flash(f"Error saving attendance: {e}", 'danger')

    return redirect(url_for('teacher.mark_attendance', subject_id=subject_id, date=attendance_date))


# -------------------------------------------------------------------------
# Attendance History
# -------------------------------------------------------------------------
@teacher_bp.route('/attendance-history')
def attendance_history():
    teacher = get_current_teacher()
    assigned_subjects = query_db("""
        SELECT s.*
        FROM teacher_subjects ts
        JOIN subjects s ON ts.subject_id = s.id
        WHERE ts.teacher_id = %s
        ORDER BY s.subject_code ASC
    """, (teacher['id'],))

    subject_filter = request.args.get('subject_id', type=int)
    date_filter = request.args.get('date')

    query = """
        SELECT a.attendance_date, sub.id as subject_id, sub.subject_code, sub.subject_name,
               sub.department, sub.year, sub.section,
               COUNT(a.id) as total_students,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM attendance a
        JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.teacher_id = %s
    """
    params = [teacher['id']]

    if subject_filter:
        query += " AND a.subject_id = %s"
        params.append(subject_filter)
    if date_filter:
        query += " AND a.attendance_date = %s"
        params.append(date_filter)

    query += """
        GROUP BY a.attendance_date, a.subject_id, sub.subject_code, sub.subject_name, 
                 sub.department, sub.year, sub.section
        ORDER BY a.attendance_date DESC, sub.subject_code ASC
    """

    sessions = query_db(query, tuple(params))
    for s in sessions:
        tot = s['total_students']
        pres = s['present_count']
        s['percentage'] = round((pres / tot * 100), 1) if tot > 0 else 0.0

    return render_template('teacher/attendance_history.html',
        sessions=sessions,
        subjects=assigned_subjects,
        selected_subject=subject_filter,
        selected_date=date_filter
    )


# -------------------------------------------------------------------------
# Reports & CSV Export
# -------------------------------------------------------------------------
@teacher_bp.route('/reports')
def reports():
    teacher = get_current_teacher()
    assigned_subjects = query_db("""
        SELECT s.*
        FROM teacher_subjects ts
        JOIN subjects s ON ts.subject_id = s.id
        WHERE ts.teacher_id = %s
        ORDER BY s.subject_code ASC
    """, (teacher['id'],))

    subject_id = request.args.get('subject_id', type=int)
    if not subject_id and assigned_subjects:
        subject_id = assigned_subjects[0]['id']

    report_data = []
    if subject_id:
        report_data = query_db("""
            SELECT s.student_id, s.name as student_name, s.department, s.year, s.section,
                   sub.subject_code, sub.subject_name,
                   COUNT(a.id) as total_classes,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
            FROM students s
            JOIN subjects sub ON sub.id = %s
            LEFT JOIN attendance a ON s.id = a.student_id AND sub.id = a.subject_id
            WHERE s.department = sub.department AND s.year = sub.year AND s.section = sub.section
            GROUP BY s.id, sub.id
            ORDER BY s.student_id ASC
        """, (subject_id,))

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

    return render_template('teacher/reports.html',
        reports=report_data,
        subjects=assigned_subjects,
        selected_subject=subject_id
    )


@teacher_bp.route('/export-csv')
def export_csv():
    teacher = get_current_teacher()
    subject_id = request.args.get('subject_id', type=int)

    if not subject_id:
        flash('Please specify a subject for report export.', 'warning')
        return redirect(url_for('teacher.reports'))

    rows = query_db("""
        SELECT s.student_id, s.name as student_name, s.department, s.year, s.section,
               sub.subject_code, sub.subject_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM students s
        JOIN subjects sub ON sub.id = %s
        LEFT JOIN attendance a ON s.id = a.student_id AND sub.id = a.subject_id
        WHERE s.department = sub.department AND s.year = sub.year AND s.section = sub.section
        GROUP BY s.id, sub.id
        ORDER BY s.student_id ASC
    """, (subject_id,))

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
        headers={"Content-disposition": f"attachment; filename=teacher_attendance_report_{subject_id}.csv"}
    )


# -------------------------------------------------------------------------
# Low Attendance Students
# -------------------------------------------------------------------------
@teacher_bp.route('/low-attendance')
def low_attendance():
    teacher = get_current_teacher()
    low_records = query_db("""
        SELECT s.student_id, s.name as student_name, s.department, s.year, s.section,
               sub.subject_code, sub.subject_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM students s
        JOIN subjects sub ON s.department = sub.department AND s.year = sub.year AND s.section = sub.section
        JOIN teacher_subjects ts ON sub.id = ts.subject_id AND ts.teacher_id = %s
        LEFT JOIN attendance a ON s.id = a.student_id AND sub.id = a.subject_id
        GROUP BY s.id, sub.id
        HAVING total_classes > 0 AND (present_count * 100.0 / total_classes) < 75.0
        ORDER BY (present_count * 100.0 / total_classes) ASC, s.student_id ASC
    """, (teacher['id'],))

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

    return render_template('teacher/low_attendance.html', records=low_records)

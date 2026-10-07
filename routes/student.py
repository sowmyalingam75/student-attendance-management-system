from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from utils.database import query_db

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
@login_required('student')
def require_student():
    pass


def get_current_student():
    """Helper to get current logged-in student info."""
    sid = session.get('username')
    return query_db("SELECT * FROM students WHERE student_id = %s", (sid,), one=True)


# -------------------------------------------------------------------------
# Student Dashboard
# -------------------------------------------------------------------------
@student_bp.route('/dashboard')
def dashboard():
    student = get_current_student()
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('auth.logout'))

    # Overall attendance statistics
    overall_stats = query_db("""
        SELECT 
            COUNT(*) as total_classes,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM attendance
        WHERE student_id = %s
    """, (student['id'],), one=True)

    total_classes = overall_stats['total_classes'] or 0
    present_count = overall_stats['present_count'] or 0
    absent_count = overall_stats['absent_count'] or 0
    overall_percentage = round((present_count / total_classes * 100), 1) if total_classes > 0 else 0.0

    # Subject-wise attendance
    subjects_attendance = query_db("""
        SELECT s.id, s.subject_code, s.subject_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM subjects s
        LEFT JOIN attendance a ON s.id = a.subject_id AND a.student_id = %s
        WHERE s.department = %s AND s.year = %s AND s.section = %s
        GROUP BY s.id
        ORDER BY s.subject_code ASC
    """, (student['id'], student['department'], student['year'], student['section']))

    has_low_subject = False
    for sub in subjects_attendance:
        tot = sub['total_classes'] or 0
        pres = sub['present_count'] or 0
        pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
        sub['percentage'] = pct
        if pct < 75 and tot > 0:
            has_low_subject = True
        if pct >= 75:
            sub['badge_class'] = 'badge-success'
            sub['status_text'] = 'Good Attendance'
        elif pct >= 65:
            sub['badge_class'] = 'badge-warning'
            sub['status_text'] = 'Low Attendance'
        else:
            sub['badge_class'] = 'badge-danger'
            sub['status_text'] = 'Critical Attendance'

    # Subject chart data
    chart_subjects = [s['subject_code'] for s in subjects_attendance]
    chart_percentages = [s['percentage'] for s in subjects_attendance]

    # Attendance overall warning condition
    is_warning = overall_percentage < 75.0 or has_low_subject

    return render_template('student/dashboard.html',
        student=student,
        total_classes=total_classes,
        present_count=present_count,
        absent_count=absent_count,
        overall_percentage=overall_percentage,
        subjects=subjects_attendance,
        is_warning=is_warning,
        chart_subjects=chart_subjects,
        chart_percentages=chart_percentages
    )


# -------------------------------------------------------------------------
# Detailed Subject Attendance
# -------------------------------------------------------------------------
@student_bp.route('/attendance')
def attendance():
    student = get_current_student()
    if not student:
        return redirect(url_for('auth.logout'))

    subjects_attendance = query_db("""
        SELECT s.id, s.subject_code, s.subject_name,
               t.name as teacher_name,
               COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM subjects s
        LEFT JOIN teacher_subjects ts ON s.id = ts.subject_id
        LEFT JOIN teachers t ON ts.teacher_id = t.id
        LEFT JOIN attendance a ON s.id = a.subject_id AND a.student_id = %s
        WHERE s.department = %s AND s.year = %s AND s.section = %s
        GROUP BY s.id, t.name
        ORDER BY s.subject_code ASC
    """, (student['id'], student['department'], student['year'], student['section']))

    for sub in subjects_attendance:
        tot = sub['total_classes'] or 0
        pres = sub['present_count'] or 0
        pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
        sub['percentage'] = pct
        if pct >= 75:
            sub['badge_class'] = 'badge-success'
            sub['status_text'] = 'Good Attendance'
        elif pct >= 65:
            sub['badge_class'] = 'badge-warning'
            sub['status_text'] = 'Low Attendance'
        else:
            sub['badge_class'] = 'badge-danger'
            sub['status_text'] = 'Critical Attendance'

    return render_template('student/attendance.html',
        student=student,
        subjects=subjects_attendance
    )


# -------------------------------------------------------------------------
# Attendance History & Records
# -------------------------------------------------------------------------
@student_bp.route('/history')
def history():
    student = get_current_student()
    if not student:
        return redirect(url_for('auth.logout'))

    subjects_list = query_db("""
        SELECT DISTINCT s.id, s.subject_code, s.subject_name
        FROM subjects s
        WHERE s.department = %s AND s.year = %s AND s.section = %s
        ORDER BY s.subject_code ASC
    """, (student['department'], student['year'], student['section']))

    subject_id = request.args.get('subject_id', type=int)
    status_filter = request.args.get('status')
    month_filter = request.args.get('month')  # format: 'YYYY-MM'

    query = """
        SELECT a.id, a.attendance_date, a.status,
               s.subject_code, s.subject_name,
               t.name as teacher_name
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        JOIN teachers t ON a.teacher_id = t.id
        WHERE a.student_id = %s
    """
    params = [student['id']]

    if subject_id:
        query += " AND a.subject_id = %s"
        params.append(subject_id)
    if status_filter:
        query += " AND a.status = %s"
        params.append(status_filter)
    if month_filter:
        query += " AND a.attendance_date LIKE %s"
        params.append(f"{month_filter}%")

    query += " ORDER BY a.attendance_date DESC, a.id DESC"

    records = query_db(query, tuple(params))

    # Distinct months for month filter dropdown
    distinct_months = query_db("""
        SELECT DISTINCT SUBSTR(attendance_date, 1, 7) as month_val
        FROM attendance
        WHERE student_id = %s
        ORDER BY month_val DESC
    """, (student['id'],))

    return render_template('student/history.html',
        student=student,
        records=records,
        subjects=subjects_list,
        distinct_months=distinct_months,
        selected_subject=subject_id,
        selected_status=status_filter,
        selected_month=month_filter
    )

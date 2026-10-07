from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from utils.database import query_db

auth_bp = Blueprint('auth', __name__)

def login_required(allowed_roles=None):
    """
    Decorator to protect routes requiring authentication and optional role authorization.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('role')
            if allowed_roles:
                if isinstance(allowed_roles, str) and user_role != allowed_roles:
                    flash('You do not have permission to access that page.', 'danger')
                    return redirect_to_dashboard(user_role)
                elif isinstance(allowed_roles, (list, tuple)) and user_role not in allowed_roles:
                    flash('You do not have permission to access that page.', 'danger')
                    return redirect_to_dashboard(user_role)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def redirect_to_dashboard(role):
    """Helper to redirect authenticated users to their corresponding dashboard."""
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif role == 'student':
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to respective dashboard
    if 'user_id' in session:
        return redirect_to_dashboard(session.get('role'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html', username=username)

        # Look up user in database
        user = query_db("SELECT * FROM users WHERE username = %s", (username,), one=True)

        if user and check_password_hash(user['password'], password):
            # Setup session
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # Populate role-specific context
            if user['role'] == 'admin':
                session['name'] = 'Administrator'
                session['display_title'] = 'System Admin'
            elif user['role'] == 'teacher':
                teacher = query_db("SELECT * FROM teachers WHERE teacher_id = %s", (username,), one=True)
                if teacher:
                    session['teacher_db_id'] = teacher['id']
                    session['name'] = teacher['name']
                    session['department'] = teacher['department']
                else:
                    session['name'] = username
            elif user['role'] == 'student':
                student = query_db("SELECT * FROM students WHERE student_id = %s", (username,), one=True)
                if student:
                    session['student_db_id'] = student['id']
                    session['name'] = student['name']
                    session['department'] = student['department']
                    session['year'] = student['year']
                    session['section'] = student['section']
                else:
                    session['name'] = username

            flash(f"Welcome back, {session.get('name', username)}!", 'success')
            return redirect_to_dashboard(user['role'])
        else:
            flash('Invalid credentials. Please verify your username and password.', 'danger')
            return render_template('login.html', username=username)

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

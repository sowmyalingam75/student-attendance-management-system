import os
from datetime import datetime
from flask import Flask, redirect, url_for, session, render_template
from config import Config
from utils.database import init_database

# Create Flask application instance
app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.teacher import teacher_bp
from routes.student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(student_bp)


# -------------------------------------------------------------------------
# Template Helpers & Filters
# -------------------------------------------------------------------------
@app.template_filter('format_date')
def format_date(value, fmt='%d-%m-%Y'):
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(fmt)


@app.template_filter('badge_status')
def badge_status(percentage):
    try:
        pct = float(percentage)
    except (ValueError, TypeError):
        return 'badge-secondary', 'N/A'
    
    if pct >= 75.0:
        return 'badge-success', 'Good Attendance'
    elif pct >= 65.0:
        return 'badge-warning', 'Low Attendance'
    else:
        return 'badge-danger', 'Critical Attendance'


@app.context_processor
def inject_global_context():
    return {
        'current_year': datetime.now().year,
        'app_name': 'College Attendance Management System'
    }


# -------------------------------------------------------------------------
# Root & Error Handlers
# -------------------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


# -------------------------------------------------------------------------
# Application Entry Point
# -------------------------------------------------------------------------
if __name__ == '__main__':
    # Initialize database if needed on startup
    try:
        init_database()
    except Exception as e:
        print(f"[Startup Warning] Database auto-initialization check: {e}")

    print("==================================================")
    print(" Student Attendance Management System Running")
    print(f" URL: http://127.0.0.1:{Config.PORT}")
    print("==================================================")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)

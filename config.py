import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-college-attendance-key-2026')
    
    # MySQL Database Settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'student_attendance_db')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Engine type: 'mysql' or 'sqlite'
    DB_TYPE = os.environ.get('DB_TYPE', 'mysql').lower()
    
    # SQLite file path if fallback or testing
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'attendance.db')
    
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    PORT = int(os.environ.get('PORT', 5000))

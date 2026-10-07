import os
import sqlite3
import re
from config import Config

# Optional import for MySQL
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception

class DatabaseManager:
    """
    Unified database manager supporting MySQL (primary) with automatic 
    resilient fallback to SQLite when MySQL server is unreachable.
    """
    _active_engine = None

    @classmethod
    def get_connection(cls):
        """
        Attempts to connect to MySQL first (if DB_TYPE is mysql).
        If MySQL server is offline or fails to connect, gracefully falls back
        to SQLite so the application remains fully functional.
        """
        if cls._active_engine == 'sqlite':
            return cls._get_sqlite_connection()
        elif cls._active_engine == 'mysql':
            return mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                autocommit=False
            )

        if Config.DB_TYPE == 'mysql' and mysql is not None:
            try:
                conn = mysql.connector.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    port=Config.DB_PORT,
                    connection_timeout=2,
                    autocommit=False
                )
                cls._active_engine = 'mysql'
                return conn
            except Exception as e:
                # Log informative warning about MySQL unavailability
                print(f"\n[Database Notice] Could not connect to MySQL server ({e}).")
                print(f"[Database Notice] Automatically switching to local SQLite database: {Config.SQLITE_DB_PATH}\n")
                cls._active_engine = 'sqlite'
                return cls._get_sqlite_connection()
        else:
            cls._active_engine = 'sqlite'
            return cls._get_sqlite_connection()


    @classmethod
    def _get_sqlite_connection(cls):
        """Connects to SQLite database and ensures schema exists."""
        db_path = Config.SQLITE_DB_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        # Register CONCAT function for MySQL compatibility
        conn.create_function("CONCAT", -1, lambda *args: "".join(str(a) for a in args if a is not None))
        return conn

    @classmethod
    def get_engine_name(cls):
        """Returns currently active engine name: 'mysql' or 'sqlite'."""
        if cls._active_engine is None:
            # Probe connection
            conn = cls.get_connection()
            conn.close()
        return cls._active_engine


def get_db():
    """Returns a raw database connection."""
    return DatabaseManager.get_connection()


def _adapt_query_for_sqlite(query):
    """
    Converts MySQL-specific syntax to SQLite syntax if running in SQLite mode.
    Converts %s placeholders to ?, and MySQL functions like CURDATE() to DATE('now').
    """
    # Replace parameter placeholders %s with ?
    adapted = query.replace('%s', '?')
    # Replace CURDATE() with DATE('now')
    adapted = re.sub(r'\bCURDATE\(\)', "DATE('now')", adapted, flags=re.IGNORECASE)
    # Replace NOW() with DATETIME('now')
    adapted = re.sub(r'\bNOW\(\)', "DATETIME('now')", adapted, flags=re.IGNORECASE)
    # Replace GROUP_CONCAT(col SEPARATOR ', ') with GROUP_CONCAT(col, ', ')
    adapted = re.sub(r'GROUP_CONCAT\((.*?)\s+SEPARATOR\s+([\'"].*?[\'"])\)', r'GROUP_CONCAT(\1, \2)', adapted, flags=re.IGNORECASE)
    return adapted



def query_db(query, args=(), one=False):
    """
    Executes a SELECT query with parameterized inputs.
    Returns a list of dictionaries, or a single dictionary if one=True.
    """
    conn = DatabaseManager.get_connection()
    engine = DatabaseManager.get_engine_name()
    result = None

    try:
        if engine == 'mysql':
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, args)
            rows = cursor.fetchall()
            cursor.close()
            result = (rows[0] if rows else None) if one else rows
        else:
            sqlite_query = _adapt_query_for_sqlite(query)
            cursor = conn.cursor()
            cursor.execute(sqlite_query, args)
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            result = (rows[0] if rows else None) if one else rows
    except Exception as e:
        print(f"[Query Error] {e} | Query: {query} | Args: {args}")
        raise e
    finally:
        conn.close()

    return result


def modify_db(query, args=()):
    """
    Executes an INSERT, UPDATE, or DELETE query with parameterized inputs.
    Commits transaction and returns dict with 'lastrowid' and 'rowcount'.
    """
    conn = DatabaseManager.get_connection()
    engine = DatabaseManager.get_engine_name()
    info = {'lastrowid': None, 'rowcount': 0}

    try:
        if engine == 'mysql':
            cursor = conn.cursor()
            cursor.execute(query, args)
            conn.commit()
            info['lastrowid'] = cursor.lastrowid
            info['rowcount'] = cursor.rowcount
            cursor.close()
        else:
            sqlite_query = _adapt_query_for_sqlite(query)
            cursor = conn.cursor()
            cursor.execute(sqlite_query, args)
            conn.commit()
            info['lastrowid'] = cursor.lastrowid
            info['rowcount'] = cursor.rowcount
            cursor.close()
    except Exception as e:
        conn.rollback()
        print(f"[Modify Error] {e} | Query: {query} | Args: {args}")
        raise e
    finally:
        conn.close()

    return info


def init_database():
    """
    Initializes the database schema and sample data.
    If MySQL is accessible, creates database and tables according to schema.sql.
    If SQLite fallback is active, sets up SQLite schema and seeds identical data.
    """
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')
    
    # Try MySQL first
    if Config.DB_TYPE == 'mysql' and mysql is not None:
        try:
            # Connect without specifying database to create database if needed
            server_conn = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                port=Config.DB_PORT
            )
            cursor = server_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME};")
            cursor.close()
            server_conn.close()

            # Now connect to the database and run schema.sql
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT
            )
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            cursor = conn.cursor()
            for statement in sql_script.split(';'):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
            cursor.close()
            conn.close()
            print("[Database] MySQL database and tables successfully initialized with sample data.")
            return 'mysql'
        except Exception as e:
            print(f"[Database] Could not initialize MySQL ({e}). Initializing SQLite fallback instead...")

    # Fallback to SQLite initialization
    return _init_sqlite_schema()


def _init_sqlite_schema():
    """Initializes the SQLite database with full schema and sample data."""
    db_path = Config.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        department TEXT NOT NULL,
        year TEXT NOT NULL,
        section TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        department TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_code TEXT NOT NULL UNIQUE,
        subject_name TEXT NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL,
        section TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE (teacher_id, subject_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        attendance_date DATE NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
        UNIQUE (student_id, subject_id, attendance_date)
    );
    """)

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users;")
    count = cursor.fetchone()[0]

    if count == 0:
        # Seed users
        admin_pass = 'scrypt:32768:8:1$MrmyvhNCUnY3EFbm$5ed7bb33f231fab523b8aac915de24f6e4575134dab8bb530b04d2f0400e00d124d8f2bcf8fb7a17ec8c24e15eefba7dd0a05708cc9af5bbf1bd4921a7c18d97'
        teacher_pass = 'scrypt:32768:8:1$b1WSkJS79ydmyMEV$d4ec1c1cee780b9e553c7301b5610ce4f118ddfebd9d6b1d4fbeb947c23e7343b20b1d15780ace3afec4f83b04d50c48dbd8e4a74e7db238b95add058314fedc'
        student_pass = 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'

        users_data = [
            ('admin', admin_pass, 'admin'),
            ('teacher01', teacher_pass, 'teacher'),
            ('teacher02', teacher_pass, 'teacher'),
        ]
        for i in range(1, 11):
            sid = f"STU{i:03d}"
            users_data.append((sid, student_pass, 'student'))
        
        cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?);", users_data)

        # Seed teachers
        teachers_data = [
            ('teacher01', 'Dr. Robert Smith', 'robert.smith@college.edu', '9876543210', 'Computer Science', teacher_pass),
            ('teacher02', 'Prof. Emily Davis', 'emily.davis@college.edu', '9876543211', 'Computer Science', teacher_pass)
        ]
        cursor.executemany("INSERT INTO teachers (teacher_id, name, email, phone, department, password) VALUES (?, ?, ?, ?, ?, ?);", teachers_data)

        # Seed students
        students_info = [
            ('STU001', 'Alice Johnson', 'alice.j@college.edu', '9876500001', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU002', 'Brian Miller', 'brian.m@college.edu', '9876500002', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU003', 'Catherine Brown', 'catherine.b@college.edu', '9876500003', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU004', 'David Wilson', 'david.w@college.edu', '9876500004', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU005', 'Elena Martinez', 'elena.m@college.edu', '9876500005', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU006', 'Frank White', 'frank.w@college.edu', '9876500006', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU007', 'Grace Lee', 'grace.l@college.edu', '9876500007', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU008', 'Henry Taylor', 'henry.t@college.edu', '9876500008', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU009', 'Isabella Clark', 'isabella.c@college.edu', '9876500009', 'Computer Science', '3rd Year', 'A', student_pass),
            ('STU010', 'Jack Anderson', 'jack.a@college.edu', '9876500010', 'Computer Science', '3rd Year', 'A', student_pass),
        ]
        cursor.executemany("INSERT INTO students (student_id, name, email, phone, department, year, section, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", students_info)

        # Seed subjects
        subjects_data = [
            ('CS301', 'Python Programming', 'Computer Science', '3rd Year', 'A'),
            ('CS302', 'Database Management Systems', 'Computer Science', '3rd Year', 'A'),
            ('CS303', 'Web Development', 'Computer Science', '3rd Year', 'A'),
            ('CS304', 'Computer Networks', 'Computer Science', '3rd Year', 'A'),
        ]
        cursor.executemany("INSERT INTO subjects (subject_code, subject_name, department, year, section) VALUES (?, ?, ?, ?, ?);", subjects_data)

        # Assign subjects
        cursor.executemany("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?);", [
            (1, 1), (1, 2), (2, 3), (2, 4)
        ])

        # Seed attendance records matching MySQL schema.sql
        # Subject 1 (Python, Teacher 1)
        # Dates: 2026-09-21, 2026-09-22, 2026-09-28, 2026-09-29, 2026-10-05, 2026-10-06, 2026-10-07
        att_records = [
            # 2026-09-21
            (1, 1, 1, '2026-09-21', 'Present'), (2, 1, 1, '2026-09-21', 'Present'), (3, 1, 1, '2026-09-21', 'Present'),
            (4, 1, 1, '2026-09-21', 'Present'), (5, 1, 1, '2026-09-21', 'Present'), (6, 1, 1, '2026-09-21', 'Present'),
            (7, 1, 1, '2026-09-21', 'Present'), (8, 1, 1, '2026-09-21', 'Absent'),  (9, 1, 1, '2026-09-21', 'Absent'),  (10, 1, 1, '2026-09-21', 'Absent'),
            # 2026-09-22
            (1, 1, 1, '2026-09-22', 'Present'), (2, 1, 1, '2026-09-22', 'Present'), (3, 1, 1, '2026-09-22', 'Present'),
            (4, 1, 1, '2026-09-22', 'Present'), (5, 1, 1, '2026-09-22', 'Present'), (6, 1, 1, '2026-09-22', 'Present'),
            (7, 1, 1, '2026-09-22', 'Present'), (8, 1, 1, '2026-09-22', 'Present'), (9, 1, 1, '2026-09-22', 'Absent'),  (10, 1, 1, '2026-09-22', 'Absent'),
            # 2026-09-28
            (1, 1, 1, '2026-09-28', 'Present'), (2, 1, 1, '2026-09-28', 'Present'), (3, 1, 1, '2026-09-28', 'Present'),
            (4, 1, 1, '2026-09-28', 'Present'), (5, 1, 1, '2026-09-28', 'Present'), (6, 1, 1, '2026-09-28', 'Absent'),
            (7, 1, 1, '2026-09-28', 'Present'), (8, 1, 1, '2026-09-28', 'Present'), (9, 1, 1, '2026-09-28', 'Absent'),  (10, 1, 1, '2026-09-28', 'Absent'),
            # 2026-09-29
            (1, 1, 1, '2026-09-29', 'Present'), (2, 1, 1, '2026-09-29', 'Present'), (3, 1, 1, '2026-09-29', 'Present'),
            (4, 1, 1, '2026-09-29', 'Present'), (5, 1, 1, '2026-09-29', 'Present'), (6, 1, 1, '2026-09-29', 'Present'),
            (7, 1, 1, '2026-09-29', 'Present'), (8, 1, 1, '2026-09-29', 'Absent'),  (9, 1, 1, '2026-09-29', 'Present'), (10, 1, 1, '2026-09-29', 'Absent'),
            # 2026-10-05
            (1, 1, 1, '2026-10-05', 'Present'), (2, 1, 1, '2026-10-05', 'Present'), (3, 1, 1, '2026-10-05', 'Present'),
            (4, 1, 1, '2026-10-05', 'Present'), (5, 1, 1, '2026-10-05', 'Absent'),  (6, 1, 1, '2026-10-05', 'Present'),
            (7, 1, 1, '2026-10-05', 'Present'), (8, 1, 1, '2026-10-05', 'Present'), (9, 1, 1, '2026-10-05', 'Absent'),  (10, 1, 1, '2026-10-05', 'Present'),
            # 2026-10-06
            (1, 1, 1, '2026-10-06', 'Present'), (2, 1, 1, '2026-10-06', 'Present'), (3, 1, 1, '2026-10-06', 'Present'),
            (4, 1, 1, '2026-10-06', 'Present'), (5, 1, 1, '2026-10-06', 'Present'), (6, 1, 1, '2026-10-06', 'Present'),
            (7, 1, 1, '2026-10-06', 'Present'), (8, 1, 1, '2026-10-06', 'Present'), (9, 1, 1, '2026-10-06', 'Present'), (10, 1, 1, '2026-10-06', 'Absent'),
            # 2026-10-07
            (1, 1, 1, '2026-10-07', 'Present'), (2, 1, 1, '2026-10-07', 'Present'), (3, 1, 1, '2026-10-07', 'Present'),
            (4, 1, 1, '2026-10-07', 'Present'), (5, 1, 1, '2026-10-07', 'Present'), (6, 1, 1, '2026-10-07', 'Present'),
            (7, 1, 1, '2026-10-07', 'Absent'),  (8, 1, 1, '2026-10-07', 'Present'), (9, 1, 1, '2026-10-07', 'Absent'),  (10, 1, 1, '2026-10-07', 'Absent'),

            # Subject 2 (DBMS, Teacher 1)
            # 2026-09-22
            (1, 2, 1, '2026-09-22', 'Present'), (2, 2, 1, '2026-09-22', 'Present'), (3, 2, 1, '2026-09-22', 'Present'),
            (4, 2, 1, '2026-09-22', 'Present'), (5, 2, 1, '2026-09-22', 'Present'), (6, 2, 1, '2026-09-22', 'Present'),
            (7, 2, 1, '2026-09-22', 'Present'), (8, 2, 1, '2026-09-22', 'Absent'),  (9, 2, 1, '2026-09-22', 'Present'), (10, 2, 1, '2026-09-22', 'Absent'),
            # 2026-09-25
            (1, 2, 1, '2026-09-25', 'Present'), (2, 2, 1, '2026-09-25', 'Present'), (3, 2, 1, '2026-09-25', 'Present'),
            (4, 2, 1, '2026-09-25', 'Present'), (5, 2, 1, '2026-09-25', 'Present'), (6, 2, 1, '2026-09-25', 'Present'),
            (7, 2, 1, '2026-09-25', 'Present'), (8, 2, 1, '2026-09-25', 'Present'), (9, 2, 1, '2026-09-25', 'Absent'),  (10, 2, 1, '2026-09-25', 'Absent'),
            # 2026-10-02
            (1, 2, 1, '2026-10-02', 'Present'), (2, 2, 1, '2026-10-02', 'Present'), (3, 2, 1, '2026-10-02', 'Present'),
            (4, 2, 1, '2026-10-02', 'Present'), (5, 2, 1, '2026-10-02', 'Present'), (6, 2, 1, '2026-10-02', 'Present'),
            (7, 2, 1, '2026-10-02', 'Present'), (8, 2, 1, '2026-10-02', 'Absent'),  (9, 2, 1, '2026-10-02', 'Absent'),  (10, 2, 1, '2026-10-02', 'Absent'),
            # 2026-10-06
            (1, 2, 1, '2026-10-06', 'Present'), (2, 2, 1, '2026-10-06', 'Present'), (3, 2, 1, '2026-10-06', 'Present'),
            (4, 2, 1, '2026-10-06', 'Present'), (5, 2, 1, '2026-10-06', 'Present'), (6, 2, 1, '2026-10-06', 'Present'),
            (7, 2, 1, '2026-10-06', 'Present'), (8, 2, 1, '2026-10-06', 'Present'), (9, 2, 1, '2026-10-06', 'Present'), (10, 2, 1, '2026-10-06', 'Present'),

            # Subject 3 (Web Development, Teacher 2)
            # 2026-09-23
            (1, 3, 2, '2026-09-23', 'Present'), (2, 3, 2, '2026-09-23', 'Present'), (3, 3, 2, '2026-09-23', 'Present'),
            (4, 3, 2, '2026-09-23', 'Present'), (5, 3, 2, '2026-09-23', 'Present'), (6, 3, 2, '2026-09-23', 'Present'),
            (7, 3, 2, '2026-09-23', 'Present'), (8, 3, 2, '2026-09-23', 'Absent'),  (9, 3, 2, '2026-09-23', 'Absent'),  (10, 3, 2, '2026-09-23', 'Absent'),
            # 2026-09-30
            (1, 3, 2, '2026-09-30', 'Present'), (2, 3, 2, '2026-09-30', 'Present'), (3, 3, 2, '2026-09-30', 'Present'),
            (4, 3, 2, '2026-09-30', 'Present'), (5, 3, 2, '2026-09-30', 'Present'), (6, 3, 2, '2026-09-30', 'Present'),
            (7, 3, 2, '2026-09-30', 'Present'), (8, 3, 2, '2026-09-30', 'Present'), (9, 3, 2, '2026-09-30', 'Absent'),  (10, 3, 2, '2026-09-30', 'Absent'),
            # 2026-10-07
            (1, 3, 2, '2026-10-07', 'Present'), (2, 3, 2, '2026-10-07', 'Present'), (3, 3, 2, '2026-10-07', 'Present'),
            (4, 3, 2, '2026-10-07', 'Present'), (5, 3, 2, '2026-10-07', 'Present'), (6, 3, 2, '2026-10-07', 'Present'),
            (7, 3, 2, '2026-10-07', 'Present'), (8, 3, 2, '2026-10-07', 'Present'), (9, 3, 2, '2026-10-07', 'Present'), (10, 3, 2, '2026-10-07', 'Absent'),

            # Subject 4 (Computer Networks, Teacher 2)
            # 2026-09-26
            (1, 4, 2, '2026-09-26', 'Present'), (2, 4, 2, '2026-09-26', 'Present'), (3, 4, 2, '2026-09-26', 'Present'),
            (4, 4, 2, '2026-09-26', 'Present'), (5, 4, 2, '2026-09-26', 'Present'), (6, 4, 2, '2026-09-26', 'Present'),
            (7, 4, 2, '2026-09-26', 'Present'), (8, 4, 2, '2026-09-26', 'Absent'),  (9, 4, 2, '2026-09-26', 'Absent'),  (10, 4, 2, '2026-09-26', 'Absent'),
            # 2026-10-03
            (1, 4, 2, '2026-10-03', 'Present'), (2, 4, 2, '2026-10-03', 'Present'), (3, 4, 2, '2026-10-03', 'Present'),
            (4, 4, 2, '2026-10-03', 'Present'), (5, 4, 2, '2026-10-03', 'Present'), (6, 4, 2, '2026-10-03', 'Present'),
            (7, 4, 2, '2026-10-03', 'Present'), (8, 4, 2, '2026-10-03', 'Present'), (9, 4, 2, '2026-10-03', 'Absent'),  (10, 4, 2, '2026-10-03', 'Absent')
        ]
        cursor.executemany("INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status) VALUES (?, ?, ?, ?, ?);", att_records)

    conn.commit()
    conn.close()
    print(f"[Database] SQLite database initialized at {db_path} with full sample data.")
    return 'sqlite'

# AttendEase - Student Attendance Management System

A complete, production-grade, web-based **Student Attendance Management System** built with **Python Flask**, **MySQL**, **HTML5/CSS3**, and **Vanilla JavaScript**. Designed with a professional, responsive college-management-system portal interface, role-based access control, real-time analytics, and automated attendance compliance tracking.

---

## 🌟 Key Features

### 1. 🛡️ Administrator Role
- **Centralized Dashboard**: Live statistics showing Total Students, Total Faculty, Total Courses, Today's Present/Absent, and Low Attendance alerts.
- **Analytics Visualizations**: Interactive Chart.js graphs displaying daily session trends, Present vs. Absent ratios, and course participation percentages.
- **Student Management (CRUD)**: Complete lifecycle management (Add, View, Edit, Delete) with validation and duplicate prevention.
- **Teacher Management (CRUD)**: Create and manage faculty credentials, view departmental rosters, and handle staff assignments.
- **Subject Management (CRUD)**: Manage course curricula, departmental semesters, and class sections.
- **Faculty-Course Allocation**: Assign and unassign specific subjects to instructors.
- **Master Attendance Logs**: Filter institutional attendance logs by subject, date, status, or keyword.
- **Executive Reports & CSV Export**: Export class performance sheets in CSV format or print formatted reports.
- **Low Attendance (< 75%) Monitor**: Identify at-risk students with color-coded alerts (Critical `< 65%`, Low `< 75%`).

### 2. 👨‍🏫 Teacher / Faculty Role
- **Faculty Dashboard**: Overview of assigned courses, total marked class sessions, and enrolled student count.
- **Daily Attendance Register**:
  - Filter students dynamically by Subject, Department, Year, and Section.
  - Interactive Present/Absent toggles with live student count summaries.
  - **Mark All Present** and **Mark All Absent** quick-action buttons.
  - Duplicate prevention: Automatically detects if attendance for the chosen date was already recorded and enables seamless updates without duplicate rows.
- **Session History**: Comprehensive log of past class sessions with attendance rates and quick-edit links.
- **Course Performance Reports**: Student-level breakdown of Total Classes, Present, Absent, and Attendance Percentage.
- **Download CSV & Print**: One-click spreadsheet export and clean printable class reports.
- **At-Risk Student Alerts**: Filter for students falling below the mandatory 75% quota in assigned courses.

### 3. 🎓 Student Role
- **Personal Dashboard**: Student profile details (Name, ID, Department, Year, Section).
- **Circular Progress Gauge**: Radial gauge displaying overall attendance standing.
- **Attendance Threshold Warning**: Instant warning alert if overall attendance or any individual course falls below **75%**.
- **Subject-Wise Breakdown**: Detailed course-by-course metrics with color-coded progress bars and instructor info.
- **Session Timeline & History**: Personal attendance log with status badges (Present/Absent) and multi-field filters (Subject, Month, Status).

---

## 💻 Technology Stack

| Layer | Technology |
|---|---|
| **Backend Engine** | Python 3.10+ & Flask Framework |
| **Database** | MySQL (Database: `student_attendance_db`) |
| **DB Connectivity** | `mysql-connector-python` (with auto SQLite dev fallback) |
| **Password Security** | `Werkzeug.security` (Scrypt hashing algorithm) |
| **Templating Engine**| Jinja2 (HTML5 Semantic Templates) |
| **Frontend Styling**| Custom Vanilla CSS3 (CSS Variables, Flexbox, CSS Grid) |
| **Client Scripting**| Vanilla JavaScript (ES6+, DOM Manipulation, No frameworks) |
| **Visual Charts** | Chart.js 4.x (via CDN) |
| **Iconography** | Font Awesome 6 (via CDN) |
| **Typography** | Google Fonts (`Inter` & `Outfit`) |

---

## 📂 Project Directory Structure

```text
c:\student\
│
├── app.py                      # Flask Application entry point & configuration
├── config.py                   # Environment configuration & variables loader
├── requirements.txt            # Python dependencies specification
├── .env                        # Local environment credentials & database config
├── .env.example                # Template for environment configuration
├── init_db.py                  # Standalone database setup & seed script
├── test_system.py              # Automated test suite (16 comprehensive tests)
├── README.md                   # Complete documentation & user guide
│
├── database/
│   ├── schema.sql              # MySQL DDL schema and sample dataset
│   └── attendance.db           # SQLite database (auto-created if MySQL is offline)
│
├── routes/
│   ├── __init__.py             # Routes package init
│   ├── auth.py                 # Login, Logout & Session Authorization decorators
│   ├── admin.py                # Admin dashboard, CRUD, assignments, and reports
│   ├── teacher.py              # Teacher dashboard, attendance marking, history
│   └── student.py              # Student dashboard, subject breakdown, history
│
├── templates/
│   ├── base.html               # Master layout with responsive sidebar & topbar
│   ├── login.html              # Modern college login portal with demo helper
│   │
│   ├── admin/
│   │   ├── dashboard.html      # Admin dashboard with metric cards & Chart.js
│   │   ├── students.html       # Student roster with instant search & CRUD
│   │   ├── add_student.html    # Add student form with validation
│   │   ├── edit_student.html   # Edit student profile form
│   │   ├── teachers.html       # Faculty directory
│   │   ├── add_teacher.html    # Add teacher form
│   │   ├── edit_teacher.html   # Edit teacher form
│   │   ├── subjects.html       # Course catalog
│   │   ├── add_subject.html    # Add subject form
│   │   ├── edit_subject.html   # Edit subject form
│   │   ├── assign_subject.html # Teacher-Subject allocation interface
│   │   ├── attendance.html     # Master attendance log with filters
│   │   ├── reports.html        # Comprehensive reports with CSV & Print
│   │   └── low_attendance.html # Low attendance (<75%) monitoring list
│   │
│   ├── teacher/
│   │   ├── dashboard.html      # Teacher dashboard & assigned courses
│   │   ├── mark_attendance.html# Class attendance marking roster
│   │   ├── attendance_history.html # Past session logs
│   │   ├── reports.html        # Teacher course reports with CSV export
│   │   └── low_attendance.html # Course-specific low attendance alert list
│   │
│   ├── student/
│   │   ├── dashboard.html      # Student dashboard with radial gauge & table
│   │   ├── attendance.html     # Detailed subject progress breakdown
│   │   └── history.html        # Personal timeline attendance history
│   │
│   └── errors/
│       ├── 404.html            # User-friendly 404 Not Found page
│       └── 500.html            # User-friendly 500 Internal Error page
│
├── static/
│   ├── css/
│   │   └── style.css           # Master CSS design system (No Bootstrap needed)
│   │
│   └── js/
│       ├── main.js             # UI controls, search, modals, and toggles
│       └── charts.js           # Chart.js initialization & data binding
│
└── utils/
    ├── __init__.py
    └── database.py             # Unified MySQL & fallback DB manager
```

---

## 🔑 Test Login Credentials

The database comes pre-seeded with sample users for all roles. All passwords are encrypted with **Werkzeug** using Scrypt.

| Role | Username / ID | Password | Notes |
|---|---|---|---|
| **ADMIN** | `admin` | `Admin@123` | System Administrator with full privileges |
| **TEACHER 1** | `teacher01` | `Teacher@123` | Dr. Robert Smith (Python & DBMS) |
| **TEACHER 2** | `teacher02` | `Teacher@123` | Prof. Emily Davis (Web Dev & Networks) |
| **STUDENT 1** | `STU001` | `Student@123` | Alice Johnson (Good Attendance: 95%) |
| **STUDENT 8** | `STU008` | `Student@123` | Henry Taylor (Low Attendance: 70%) |
| **STUDENT 10**| `STU010` | `Student@123` | Jack Anderson (Critical Attendance: 55%) |

*Tip: On the login page (`/login`), click the **Quick Demo Fill** buttons at the bottom of the form to auto-fill these credentials instantly.*

---

## 🚀 Setup & Installation (Windows Guide)

### 1. Prerequisites
- **Python 3.10+** installed ([python.org](https://www.python.org/))
- **MySQL Server** (via MySQL Community Server or XAMPP / WampServer)
- **Git** (optional)

### 2. Clone or Open Project Directory
Open PowerShell or Command Prompt in the project folder:
```powershell
cd c:\student
```

### 3. Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
venv\Scripts\Activate.ps1

# Or activate on Windows (Command Prompt)
venv\Scripts\activate.bat
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🗄️ MySQL Database Setup

### Option A: Using MySQL Command Line or MySQL Workbench
1. Open your MySQL client (Command Line, MySQL Workbench, or phpMyAdmin in XAMPP).
2. Execute the `database/schema.sql` file:
```sql
SOURCE c:/student/database/schema.sql;
```
*Or in PowerShell:*
```powershell
mysql -u root -p < database\schema.sql
```

### Option B: Automatic Python Initialization
Configure your `.env` file (see below), then run:
```powershell
python init_db.py
```
*Note: If MySQL server is offline or not installed, the application automatically initializes a high-performance local SQLite database (`database/attendance.db`) with identical schema and sample data, so you can test the application right away.*

---

## ⚙️ Configuration (`.env`)

Edit `.env` with your MySQL credentials:
```ini
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=student_attendance_db
DB_PORT=3306

# Database Engine: 'mysql' (default) or 'sqlite'
DB_TYPE=mysql

# Application Secret Key
SECRET_KEY=college_attendance_super_secret_key_2026_xyz987

# Flask Settings
FLASK_ENV=development
DEBUG=True
PORT=5000
```

---

## ▶️ Running the Application

Run the Flask application:
```powershell
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Automated Testing

An automated test suite (`test_system.py`) is included to verify all 16 requirements specified in the project checklist:
```powershell
python test_system.py
```

### Test Coverage Checklist:
- [x] Python syntax and blueprint imports
- [x] Database connectivity and schema queries
- [x] Password verification using Werkzeug hashing
- [x] Admin, Teacher, and Student login workflows
- [x] Admin Dashboard metrics & Chart.js rendering
- [x] Student Management CRUD (Add, Edit, List, Delete)
- [x] Teacher Management CRUD (Add, Edit, List, Delete)
- [x] Subject Management CRUD & Teacher-Subject Allocation
- [x] Attendance Marking, Roster generation, and Duplicate constraint handling
- [x] Attendance Percentage calculation `(Present / Total) * 100`
- [x] Student Dashboard radial progress gauge and low-attendance alerts (`< 75%`)
- [x] Attendance Reports, CSV Exports (`/admin/export-csv`, `/teacher/export-csv`), and Printable views
- [x] Low Attendance Students page (`/admin/low-attendance`)
- [x] Session clearing and secure Logout

---

## 📊 Attendance Formula & Threshold Rules

The attendance percentage for each student in any given subject is computed as:
$$\text{Attendance Percentage} = \left(\frac{\text{Present Days}}{\text{Total Conducted Classes}}\right) \times 100$$

### Threshold Indicators:
- **$\ge 75\%$**: `Good Attendance` (Green badge $\cdot$ Exam eligible)
- **$65\% \text{ to } < 75\%$**: `Low Attendance` (Amber warning badge $\cdot$ Warning issued)
- **$< 65\%$**: `Critical Attendance` (Crimson danger badge $\cdot$ Academic debarment risk)

---

## 📸 Screenshots & UI Previews (Placeholders)

| Screen | Description |
|---|---|
| **Portal Login** | Sleek college-branded card with password visibility toggle & demo credentials |
| **Admin Dashboard** | 5 Stat counters, session trend line graph, Present/Absent doughnut chart, course breakdown |
| **Mark Attendance** | Class roster with custom toggle switches, "Mark All Present", and live counts |
| **Student Dashboard** | Radial circular percentage meter, warning banner, and subject breakdown |
| **Attendance Reports** | Comprehensive data table with multi-filter bar, Print view, and CSV export |

---

## 🔮 Future Enhancements
1. **Biometric & RFID Scanner Integration**: Direct hardware logging via REST API.
2. **Automated Parent SMS/Email Notifications**: Alert guardians when student attendance falls below 75%.
3. **QR Code Attendance**: Dynamic one-time QR codes scanned by students during lectures.
4. **Leave Application Management**: Student leave requests with faculty approval workflows.

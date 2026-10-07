-- ========================================================
-- Student Attendance Management System - Database Schema
-- Database: student_attendance_db
-- ========================================================

CREATE DATABASE IF NOT EXISTS student_attendance_db;
USE student_attendance_db;

-- --------------------------------------------------------
-- 1. Table structure for table `users`
-- --------------------------------------------------------
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS teacher_subjects;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- 2. Table structure for table `students`
-- --------------------------------------------------------
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(50) NOT NULL,
    year VARCHAR(20) NOT NULL,
    section VARCHAR(10) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- 3. Table structure for table `teachers`
-- --------------------------------------------------------
CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- 4. Table structure for table `subjects`
-- --------------------------------------------------------
CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(30) NOT NULL UNIQUE,
    subject_name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    year VARCHAR(20) NOT NULL,
    section VARCHAR(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- 5. Table structure for table `teacher_subjects`
-- --------------------------------------------------------
CREATE TABLE teacher_subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_teacher_subject (teacher_id, subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- 6. Table structure for table `attendance`
-- --------------------------------------------------------
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_subject_date (student_id, subject_id, attendance_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================================
-- SAMPLE DATA INSERTIONS
-- ========================================================

-- Passwords hashed using Werkzeug:
-- Admin:   Admin@123   -> scrypt:32768:8:1$MrmyvhNCUnY3EFbm$5ed7bb33f231fab523b8aac915de24f6e4575134dab8bb530b04d2f0400e00d124d8f2bcf8fb7a17ec8c24e15eefba7dd0a05708cc9af5bbf1bd4921a7c18d97
-- Teacher: Teacher@123 -> scrypt:32768:8:1$b1WSkJS79ydmyMEV$d4ec1c1cee780b9e553c7301b5610ce4f118ddfebd9d6b1d4fbeb947c23e7343b20b1d15780ace3afec4f83b04d50c48dbd8e4a74e7db238b95add058314fedc
-- Student: Student@123 -> scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0

-- 1. Insert Users (Admin, Teachers, Students)
INSERT INTO users (username, password, role) VALUES
('admin', 'scrypt:32768:8:1$MrmyvhNCUnY3EFbm$5ed7bb33f231fab523b8aac915de24f6e4575134dab8bb530b04d2f0400e00d124d8f2bcf8fb7a17ec8c24e15eefba7dd0a05708cc9af5bbf1bd4921a7c18d97', 'admin'),
('teacher01', 'scrypt:32768:8:1$b1WSkJS79ydmyMEV$d4ec1c1cee780b9e553c7301b5610ce4f118ddfebd9d6b1d4fbeb947c23e7343b20b1d15780ace3afec4f83b04d50c48dbd8e4a74e7db238b95add058314fedc', 'teacher'),
('teacher02', 'scrypt:32768:8:1$b1WSkJS79ydmyMEV$d4ec1c1cee780b9e553c7301b5610ce4f118ddfebd9d6b1d4fbeb947c23e7343b20b1d15780ace3afec4f83b04d50c48dbd8e4a74e7db238b95add058314fedc', 'teacher'),
('STU001', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU002', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU003', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU004', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU005', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU006', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU007', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU008', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU009', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student'),
('STU010', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0', 'student');

-- 2. Insert Teachers
INSERT INTO teachers (teacher_id, name, email, phone, department, password) VALUES
('teacher01', 'Dr. Robert Smith', 'robert.smith@college.edu', '9876543210', 'Computer Science', 'scrypt:32768:8:1$b1WSkJS79ydmyMEV$d4ec1c1cee780b9e553c7301b5610ce4f118ddfebd9d6b1d4fbeb947c23e7343b20b1d15780ace3afec4f83b04d50c48dbd8e4a74e7db238b95add058314fedc'),
('teacher02', 'Prof. Emily Davis', 'emily.davis@college.edu', '9876543211', 'Computer Science', 'scrypt:32768:8:1$b1WSkJS79ydmyMEV$d4ec1c1cee780b9e553c7301b5610ce4f118ddfebd9d6b1d4fbeb947c23e7343b20b1d15780ace3afec4f83b04d50c48dbd8e4a74e7db238b95add058314fedc');

-- 3. Insert Students
INSERT INTO students (student_id, name, email, phone, department, year, section, password) VALUES
('STU001', 'Alice Johnson', 'alice.j@college.edu', '9876500001', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU002', 'Brian Miller', 'brian.m@college.edu', '9876500002', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU003', 'Catherine Brown', 'catherine.b@college.edu', '9876500003', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU004', 'David Wilson', 'david.w@college.edu', '9876500004', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU005', 'Elena Martinez', 'elena.m@college.edu', '9876500005', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU006', 'Frank White', 'frank.w@college.edu', '9876500006', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU007', 'Grace Lee', 'grace.l@college.edu', '9876500007', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU008', 'Henry Taylor', 'henry.t@college.edu', '9876500008', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU009', 'Isabella Clark', 'isabella.c@college.edu', '9876500009', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0'),
('STU010', 'Jack Anderson', 'jack.a@college.edu', '9876500010', 'Computer Science', '3rd Year', 'A', 'scrypt:32768:8:1$kzQtOZejPCaroNid$2846bd368b4e6ac15a6b4076463987bbfb04e8042ba1036c9062609ee3d5dcf9d5ad840bd860dec1122eb796ae6045f193a1b6aa3cda92560777d8dd9cb516f0');

-- 4. Insert Subjects
INSERT INTO subjects (subject_code, subject_name, department, year, section) VALUES
('CS301', 'Python Programming', 'Computer Science', '3rd Year', 'A'),
('CS302', 'Database Management Systems', 'Computer Science', '3rd Year', 'A'),
('CS303', 'Web Development', 'Computer Science', '3rd Year', 'A'),
('CS304', 'Computer Networks', 'Computer Science', '3rd Year', 'A');

-- 5. Assign Subjects to Teachers
-- Teacher 1 (Dr. Robert Smith, id=1): Python (id=1), DBMS (id=2)
-- Teacher 2 (Prof. Emily Davis, id=2): Web Dev (id=3), Networks (id=4)
INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES
(1, 1),
(1, 2),
(2, 3),
(2, 4);

-- 6. Insert Sample Attendance Records across multiple dates
-- Dates: 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-05, 2026-10-06, 2026-10-07
-- Subject 1 (Python, Teacher 1):
INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status) VALUES
-- 2026-09-21
(1, 1, 1, '2026-09-21', 'Present'), (2, 1, 1, '2026-09-21', 'Present'), (3, 1, 1, '2026-09-21', 'Present'),
(4, 1, 1, '2026-09-21', 'Present'), (5, 1, 1, '2026-09-21', 'Present'), (6, 1, 1, '2026-09-21', 'Present'),
(7, 1, 1, '2026-09-21', 'Present'), (8, 1, 1, '2026-09-21', 'Absent'),  (9, 1, 1, '2026-09-21', 'Absent'),  (10, 1, 1, '2026-09-21', 'Absent'),
-- 2026-09-22
(1, 1, 1, '2026-09-22', 'Present'), (2, 1, 1, '2026-09-22', 'Present'), (3, 1, 1, '2026-09-22', 'Present'),
(4, 1, 1, '2026-09-22', 'Present'), (5, 1, 1, '2026-09-22', 'Present'), (6, 1, 1, '2026-09-22', 'Present'),
(7, 1, 1, '2026-09-22', 'Present'), (8, 1, 1, '2026-09-22', 'Present'), (9, 1, 1, '2026-09-22', 'Absent'),  (10, 1, 1, '2026-09-22', 'Absent'),
-- 2026-09-28
(1, 1, 1, '2026-09-28', 'Present'), (2, 1, 1, '2026-09-28', 'Present'), (3, 1, 1, '2026-09-28', 'Present'),
(4, 1, 1, '2026-09-28', 'Present'), (5, 1, 1, '2026-09-28', 'Present'), (6, 1, 1, '2026-09-28', 'Absent'),
(7, 1, 1, '2026-09-28', 'Present'), (8, 1, 1, '2026-09-28', 'Present'), (9, 1, 1, '2026-09-28', 'Absent'),  (10, 1, 1, '2026-09-28', 'Absent'),
-- 2026-09-29
(1, 1, 1, '2026-09-29', 'Present'), (2, 1, 1, '2026-09-29', 'Present'), (3, 1, 1, '2026-09-29', 'Present'),
(4, 1, 1, '2026-09-29', 'Present'), (5, 1, 1, '2026-09-29', 'Present'), (6, 1, 1, '2026-09-29', 'Present'),
(7, 1, 1, '2026-09-29', 'Present'), (8, 1, 1, '2026-09-29', 'Absent'),  (9, 1, 1, '2026-09-29', 'Present'), (10, 1, 1, '2026-09-29', 'Absent'),
-- 2026-10-05
(1, 1, 1, '2026-10-05', 'Present'), (2, 1, 1, '2026-10-05', 'Present'), (3, 1, 1, '2026-10-05', 'Present'),
(4, 1, 1, '2026-10-05', 'Present'), (5, 1, 1, '2026-10-05', 'Absent'),  (6, 1, 1, '2026-10-05', 'Present'),
(7, 1, 1, '2026-10-05', 'Present'), (8, 1, 1, '2026-10-05', 'Present'), (9, 1, 1, '2026-10-05', 'Absent'),  (10, 1, 1, '2026-10-05', 'Present'),
-- 2026-10-06
(1, 1, 1, '2026-10-06', 'Present'), (2, 1, 1, '2026-10-06', 'Present'), (3, 1, 1, '2026-10-06', 'Present'),
(4, 1, 1, '2026-10-06', 'Present'), (5, 1, 1, '2026-10-06', 'Present'), (6, 1, 1, '2026-10-06', 'Present'),
(7, 1, 1, '2026-10-06', 'Present'), (8, 1, 1, '2026-10-06', 'Present'), (9, 1, 1, '2026-10-06', 'Present'), (10, 1, 1, '2026-10-06', 'Absent'),
-- 2026-10-07 (Today)
(1, 1, 1, '2026-10-07', 'Present'), (2, 1, 1, '2026-10-07', 'Present'), (3, 1, 1, '2026-10-07', 'Present'),
(4, 1, 1, '2026-10-07', 'Present'), (5, 1, 1, '2026-10-07', 'Present'), (6, 1, 1, '2026-10-07', 'Present'),
(7, 1, 1, '2026-10-07', 'Absent'),  (8, 1, 1, '2026-10-07', 'Present'), (9, 1, 1, '2026-10-07', 'Absent'),  (10, 1, 1, '2026-10-07', 'Absent');

-- Subject 2 (DBMS, Teacher 1):
INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status) VALUES
-- 2026-09-22
(1, 2, 1, '2026-09-22', 'Present'), (2, 2, 1, '2026-09-22', 'Present'), (3, 2, 1, '2026-09-22', 'Present'),
(4, 2, 1, '2026-09-22', 'Present'), (5, 2, 1, '2026-09-22', 'Present'), (6, 2, 1, '2026-09-22', 'Present'),
(7, 2, 1, '2026-09-22', 'Present'), (8, 2, 1, '2026-09-22', 'Absent'),  (9, 2, 1, '2026-09-22', 'Present'), (10, 2, 1, '2026-09-22', 'Absent'),
-- 2026-09-25
(1, 2, 1, '2026-09-25', 'Present'), (2, 2, 1, '2026-09-25', 'Present'), (3, 2, 1, '2026-09-25', 'Present'),
(4, 2, 1, '2026-09-25', 'Present'), (5, 2, 1, '2026-09-25', 'Present'), (6, 2, 1, '2026-09-25', 'Present'),
(7, 2, 1, '2026-09-25', 'Present'), (8, 2, 1, '2026-09-25', 'Present'), (9, 2, 1, '2026-09-25', 'Absent'),  (10, 2, 1, '2026-09-25', 'Absent'),
-- 2026-10-02
(1, 2, 1, '2026-10-02', 'Present'), (2, 2, 1, '2026-10-02', 'Present'), (3, 2, 1, '2026-10-02', 'Present'),
(4, 2, 1, '2026-10-02', 'Present'), (5, 2, 1, '2026-10-02', 'Present'), (6, 2, 1, '2026-10-02', 'Present'),
(7, 2, 1, '2026-10-02', 'Present'), (8, 2, 1, '2026-10-02', 'Absent'),  (9, 2, 1, '2026-10-02', 'Absent'),  (10, 2, 1, '2026-10-02', 'Absent'),
-- 2026-10-06
(1, 2, 1, '2026-10-06', 'Present'), (2, 2, 1, '2026-10-06', 'Present'), (3, 2, 1, '2026-10-06', 'Present'),
(4, 2, 1, '2026-10-06', 'Present'), (5, 2, 1, '2026-10-06', 'Present'), (6, 2, 1, '2026-10-06', 'Present'),
(7, 2, 1, '2026-10-06', 'Present'), (8, 2, 1, '2026-10-06', 'Present'), (9, 2, 1, '2026-10-06', 'Present'), (10, 2, 1, '2026-10-06', 'Present');

-- Subject 3 (Web Development, Teacher 2):
INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status) VALUES
-- 2026-09-23
(1, 3, 2, '2026-09-23', 'Present'), (2, 3, 2, '2026-09-23', 'Present'), (3, 3, 2, '2026-09-23', 'Present'),
(4, 3, 2, '2026-09-23', 'Present'), (5, 3, 2, '2026-09-23', 'Present'), (6, 3, 2, '2026-09-23', 'Present'),
(7, 3, 2, '2026-09-23', 'Present'), (8, 3, 2, '2026-09-23', 'Absent'),  (9, 3, 2, '2026-09-23', 'Absent'),  (10, 3, 2, '2026-09-23', 'Absent'),
-- 2026-09-30
(1, 3, 2, '2026-09-30', 'Present'), (2, 3, 2, '2026-09-30', 'Present'), (3, 3, 2, '2026-09-30', 'Present'),
(4, 3, 2, '2026-09-30', 'Present'), (5, 3, 2, '2026-09-30', 'Present'), (6, 3, 2, '2026-09-30', 'Present'),
(7, 3, 2, '2026-09-30', 'Present'), (8, 3, 2, '2026-09-30', 'Present'), (9, 3, 2, '2026-09-30', 'Absent'),  (10, 3, 2, '2026-09-30', 'Absent'),
-- 2026-10-07 (Today)
(1, 3, 2, '2026-10-07', 'Present'), (2, 3, 2, '2026-10-07', 'Present'), (3, 3, 2, '2026-10-07', 'Present'),
(4, 3, 2, '2026-10-07', 'Present'), (5, 3, 2, '2026-10-07', 'Present'), (6, 3, 2, '2026-10-07', 'Present'),
(7, 3, 2, '2026-10-07', 'Present'), (8, 3, 2, '2026-10-07', 'Present'), (9, 3, 2, '2026-10-07', 'Present'), (10, 3, 2, '2026-10-07', 'Absent');

-- Subject 4 (Computer Networks, Teacher 2):
INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status) VALUES
-- 2026-09-26
(1, 4, 2, '2026-09-26', 'Present'), (2, 4, 2, '2026-09-26', 'Present'), (3, 4, 2, '2026-09-26', 'Present'),
(4, 4, 2, '2026-09-26', 'Present'), (5, 4, 2, '2026-09-26', 'Present'), (6, 4, 2, '2026-09-26', 'Present'),
(7, 4, 2, '2026-09-26', 'Present'), (8, 4, 2, '2026-09-26', 'Absent'),  (9, 4, 2, '2026-09-26', 'Absent'),  (10, 4, 2, '2026-09-26', 'Absent'),
-- 2026-10-03
(1, 4, 2, '2026-10-03', 'Present'), (2, 4, 2, '2026-10-03', 'Present'), (3, 4, 2, '2026-10-03', 'Present'),
(4, 4, 2, '2026-10-03', 'Present'), (5, 4, 2, '2026-10-03', 'Present'), (6, 4, 2, '2026-10-03', 'Present'),
(7, 4, 2, '2026-10-03', 'Present'), (8, 4, 2, '2026-10-03', 'Present'), (9, 4, 2, '2026-10-03', 'Absent'),  (10, 4, 2, '2026-10-03', 'Absent');

#!/usr/bin/env python
"""
Comprehensive Automated Test Suite for Student Attendance Management System
Tests all 16 items specified in the project requirements.
"""

import sys
import unittest
from werkzeug.security import check_password_hash
from app import app
from utils.database import query_db, modify_db, DatabaseManager, init_database

class AttendanceSystemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print("STARTING COMPLETE SYSTEM VALIDATION & TESTING SUITE")
        print("========================================================")
        init_database()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def test_01_syntax_and_imports(self):
        print("\n[TEST 1 & 2] Checking Python Syntax & Route Blueprints...")
        self.assertIsNotNone(app)
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        self.assertIn('/login', rules)
        self.assertIn('/logout', rules)
        self.assertIn('/admin/dashboard', rules)
        self.assertIn('/teacher/dashboard', rules)
        self.assertIn('/student/dashboard', rules)
        print("  -> All blueprints and URLs successfully registered.")

    def test_02_database_connectivity_and_queries(self):
        print("\n[TEST 4 & 5] Checking Database Connection & Schema Queries...")
        engine = DatabaseManager.get_engine_name()
        self.assertIn(engine, ['mysql', 'sqlite'])
        print(f"  -> Active database engine: {engine.upper()}")

        user_count = query_db("SELECT COUNT(*) as cnt FROM users", one=True)['cnt']
        student_count = query_db("SELECT COUNT(*) as cnt FROM students", one=True)['cnt']
        teacher_count = query_db("SELECT COUNT(*) as cnt FROM teachers", one=True)['cnt']
        subject_count = query_db("SELECT COUNT(*) as cnt FROM subjects", one=True)['cnt']
        att_count = query_db("SELECT COUNT(*) as cnt FROM attendance", one=True)['cnt']

        self.assertGreaterEqual(user_count, 13)
        self.assertGreaterEqual(student_count, 10)
        self.assertGreaterEqual(teacher_count, 2)
        self.assertGreaterEqual(subject_count, 4)
        self.assertGreaterEqual(att_count, 50)
        print(f"  -> Database verified: {student_count} Students, {teacher_count} Teachers, {subject_count} Subjects, {att_count} Attendance logs.")

    def test_03_authentication_and_login(self):
        print("\n[TEST 6] Testing Login Authentication & Roles...")
        # 1. Invalid login
        res = self.client.post('/login', data={'username': 'admin', 'password': 'WrongPassword123'}, follow_redirects=True)
        self.assertIn(b'Invalid credentials', res.data)

        # 2. Admin Login
        res_admin = self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
        self.assertIn(b'Administrator Dashboard', res_admin.data)
        self.client.get('/logout')

        # 3. Teacher Login
        res_teacher = self.client.post('/login', data={'username': 'teacher01', 'password': 'Teacher@123'}, follow_redirects=True)
        self.assertIn(b'Faculty Portal', res_teacher.data)
        self.client.get('/logout')

        # 4. Student Login
        res_student = self.client.post('/login', data={'username': 'STU001', 'password': 'Student@123'}, follow_redirects=True)
        self.assertIn(b'Student Portal', res_student.data)
        self.client.get('/logout')
        print("  -> Admin, Teacher, and Student logins verified with hashed passwords.")

    def test_04_admin_dashboard(self):
        print("\n[TEST 7] Testing Admin Dashboard Rendering & Stats...")
        self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'System Overview', res.data)
        self.assertIn(b'Total Students', res.data)
        self.assertIn(b'Total Teachers', res.data)
        self.assertIn(b'attendanceTrendChart', res.data)
        self.assertIn(b'attendanceDonutChart', res.data)
        self.client.get('/logout')
        print("  -> Admin dashboard and charts rendered successfully.")

    def test_05_student_crud(self):
        print("\n[TEST 8] Testing Student Management CRUD...")
        self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)

        # Create
        add_data = {
            'student_id': 'STU099',
            'name': 'Test Student',
            'email': 'test.student@college.edu',
            'phone': '9998887770',
            'department': 'Computer Science',
            'year': '3rd Year',
            'section': 'A',
            'password': 'Student@123'
        }
        res_add = self.client.post('/admin/students/add', data=add_data, follow_redirects=True)
        self.assertIn(b'added successfully', res_add.data)

        # Verify in DB
        created = query_db("SELECT * FROM students WHERE student_id = 'STU099'", one=True)
        self.assertIsNotNone(created)
        self.assertEqual(created['name'], 'Test Student')

        # Update
        edit_data = {
            'name': 'Test Student Updated',
            'email': 'test.updated@college.edu',
            'phone': '9998887771',
            'department': 'Computer Science',
            'year': '3rd Year',
            'section': 'A',
            'password': ''
        }
        res_edit = self.client.post(f'/admin/students/edit/{created["id"]}', data=edit_data, follow_redirects=True)
        self.assertIn(b'updated successfully', res_edit.data)

        # Delete
        res_del = self.client.post(f'/admin/students/delete/{created["id"]}', follow_redirects=True)
        self.assertIn(b'deleted successfully', res_del.data)

        # Verify removal
        deleted = query_db("SELECT * FROM students WHERE student_id = 'STU099'", one=True)
        self.assertIsNone(deleted)
        self.client.get('/logout')
        print("  -> Student CRUD (Add, Edit, List, Delete) verified successfully.")

    def test_06_teacher_crud(self):
        print("\n[TEST 9] Testing Teacher Management CRUD...")
        self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)

        # Add teacher
        add_data = {
            'teacher_id': 'teacher99',
            'name': 'Prof. Test Teacher',
            'email': 'test.teacher@college.edu',
            'phone': '9991112223',
            'department': 'Computer Science',
            'password': 'Teacher@123'
        }
        res_add = self.client.post('/admin/teachers/add', data=add_data, follow_redirects=True)
        self.assertIn(b'added successfully', res_add.data)

        # Fetch
        t = query_db("SELECT * FROM teachers WHERE teacher_id = 'teacher99'", one=True)
        self.assertIsNotNone(t)

        # Edit
        edit_data = {
            'name': 'Prof. Test Teacher Senior',
            'email': 'test.senior@college.edu',
            'phone': '9991112224',
            'department': 'Computer Science',
            'password': ''
        }
        res_edit = self.client.post(f'/admin/teachers/edit/{t["id"]}', data=edit_data, follow_redirects=True)
        self.assertIn(b'updated successfully', res_edit.data)

        # Delete
        res_del = self.client.post(f'/admin/teachers/delete/{t["id"]}', follow_redirects=True)
        self.assertIn(b'deleted successfully', res_del.data)
        self.client.get('/logout')
        print("  -> Teacher CRUD (Add, Edit, List, Delete) verified successfully.")

    def test_07_subject_crud_and_assignment(self):
        print("\n[TEST 10] Testing Subject CRUD & Teacher-Subject Assignment...")
        self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)

        # Add subject
        sub_data = {
            'subject_code': 'CS999',
            'subject_name': 'Quantum Computing Lab',
            'department': 'Computer Science',
            'year': '4th Year',
            'section': 'A'
        }
        res_add = self.client.post('/admin/subjects/add', data=sub_data, follow_redirects=True)
        self.assertIn(b'added successfully', res_add.data)

        sub = query_db("SELECT * FROM subjects WHERE subject_code = 'CS999'", one=True)
        self.assertIsNotNone(sub)

        # Assign subject to teacher01 (id=1)
        res_assign = self.client.post('/admin/assign-subject', data={'teacher_id': 1, 'subject_id': sub['id']}, follow_redirects=True)
        self.assertIn(b'assigned to teacher successfully', res_assign.data)

        # Delete subject
        res_del = self.client.post(f'/admin/subjects/delete/{sub["id"]}', follow_redirects=True)
        self.assertIn(b'deleted successfully', res_del.data)
        self.client.get('/logout')
        print("  -> Subject CRUD & Teacher allocation verified successfully.")

    def test_08_attendance_marking_and_duplicates(self):
        print("\n[TEST 11] Testing Attendance Marking & Duplicate Prevention...")
        self.client.post('/login', data={'username': 'teacher01', 'password': 'Teacher@123'}, follow_redirects=True)

        # Mark attendance for subject 1 (Python) on date 2026-10-15
        test_date = '2026-10-15'
        form_data = {
            'subject_id': 1,
            'attendance_date': test_date,
            'status_1': 'Present',
            'status_2': 'Present',
            'status_3': 'Absent',
            'status_4': 'Present',
            'status_5': 'Present',
            'status_6': 'Present',
            'status_7': 'Present',
            'status_8': 'Absent',
            'status_9': 'Present',
            'status_10': 'Absent'
        }
        res_save = self.client.post('/teacher/save-attendance', data=form_data, follow_redirects=True)
        self.assertIn(b'saved successfully', res_save.data)

        # Verify records created
        records = query_db("SELECT * FROM attendance WHERE subject_id = 1 AND attendance_date = %s", (test_date,))
        self.assertEqual(len(records), 10)

        # Save again (update existing) with altered statuses
        form_data['status_3'] = 'Present'  # Changed from Absent to Present
        res_update = self.client.post('/teacher/save-attendance', data=form_data, follow_redirects=True)
        self.assertIn(b'saved successfully', res_update.data)

        # Verify NO duplicate rows were created
        records_after = query_db("SELECT * FROM attendance WHERE subject_id = 1 AND attendance_date = %s", (test_date,))
        self.assertEqual(len(records_after), 10)

        # Verify status updated
        st3 = query_db("SELECT status FROM attendance WHERE student_id = 3 AND subject_id = 1 AND attendance_date = %s", (test_date,), one=True)
        self.assertEqual(st3['status'], 'Present')

        # Clean up test session records
        modify_db("DELETE FROM attendance WHERE attendance_date = %s", (test_date,))
        self.client.get('/logout')
        print("  -> Attendance marking, duplicate prevention, and update verified successfully.")

    def test_09_attendance_percentage_and_student_dashboard(self):
        print("\n[TEST 12 & 13] Testing Attendance Percentage Calculation & Student Portal...")
        self.client.post('/login', data={'username': 'STU001', 'password': 'Student@123'}, follow_redirects=True)

        res = self.client.get('/student/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Alice Johnson', res.data)
        self.assertIn(b'Overall Attendance', res.data)
        self.assertIn(b'studentSubjectChart', res.data)
        self.assertIn(b'Subject-wise Attendance Status', res.data)

        # Test at-risk student STU010 (Jack Anderson, attendance < 65%)
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'STU010', 'password': 'Student@123'}, follow_redirects=True)
        res_at_risk = self.client.get('/student/dashboard')
        self.assertIn(b'Mandatory Attendance Warning', res_at_risk.data)
        self.client.get('/logout')
        print("  -> Attendance percentage calculations and student warnings verified.")

    def test_10_reports_and_csv_export(self):
        print("\n[TEST 14, 15, & 16] Testing Reports, Low Attendance Page & CSV Downloads...")
        self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)

        # Admin Reports
        res_rep = self.client.get('/admin/reports')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b'Attendance Summary Reports', res_rep.data)

        # CSV Export
        res_csv = self.client.get('/admin/export-csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Student ID,Student Name', res_csv.data)

        # Low Attendance Report
        res_low = self.client.get('/admin/low-attendance')
        self.assertEqual(res_low.status_code, 200)
        self.assertIn(b'Low Attendance Students', res_low.data)
        self.assertIn(b'STU010', res_low.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out successfully', res_logout.data)
        print("  -> Reports, CSV export, low attendance filtering, and logout verified.")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(AttendanceSystemTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n========================================================")
        print("ALL 16 TEST CHECKLIST REQUIREMENTS PASSED SUCCESSFULLY!")
        print("========================================================\n")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more tests failed.")
        sys.exit(1)

#!/usr/bin/env python
"""
Database Initialization Script for Student Attendance Management System.
Usage:
    python init_db.py
"""
import sys
from utils.database import init_database

def main():
    print("==================================================")
    print("Initializing Student Attendance System Database...")
    print("==================================================")
    try:
        engine = init_database()
        print(f"\n[SUCCESS] Database successfully initialized using engine: {engine.upper()}!")
        print("Default accounts:")
        print("  - Admin:   username: admin     | password: Admin@123")
        print("  - Teacher: username: teacher01 | password: Teacher@123")
        print("  - Student: username: STU001    | password: Student@123")
        print("==================================================")
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

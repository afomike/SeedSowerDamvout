#!/usr/bin/env python3
"""
Database initialization script for Seedsowers Ministry
Creates sample courses and admin user
"""

import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Course, CourseFile

def init_database():
    """Initialize the database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(email='admin@seedsowers.org').first()
        if not admin_user:
            # Create admin user
            admin_user = User(
                id=str(uuid.uuid4()),
                email='admin@seedsowers.org',
                first_name='Admin',
                last_name='User',
                role='super_admin',
                password_hash=generate_password_hash('admin123'),
                is_active=True
            )
            db.session.add(admin_user)
            print("✅ Admin user created (email: admin@seedsowers.org, password: admin123)")
        
        # Create sample student user
        student_user = User.query.filter_by(email='student@example.com').first()
        if not student_user:
            student_user = User(
                id=str(uuid.uuid4()),
                email='student@example.com',
                first_name='John',
                last_name='Student',
                role='student',
                password_hash=generate_password_hash('student123'),
                is_active=True
            )
            db.session.add(student_user)
            print("✅ Sample student created (email: student@example.com, password: student123)")
        
        # Create the 7 training courses
        courses_data = [
            {
                'title': 'Disciples Introductory',
                'description': 'Foundation course covering discipleship basics, NBDS/ROCK Audio Series, and Die Series One. This 4-month intensive program will establish your biblical foundation.',
                'duration': '4 Months',
                'order': 1
            },
            {
                'title': 'Haseem with Practicals',
                'description': 'Intermediate course focused on practical ministry applications and spiritual development. A 2-month program building on foundational knowledge.',
                'duration': '2 Months',
                'order': 2
            },
            {
                'title': 'Faith & Prayer Course',
                'description': 'Advanced 4-month course featuring Kenneth Hagin teachings, comprehensive prayer training, and missionary preparation package.',
                'duration': '4 Months',
                'order': 3
            },
            {
                'title': 'Ministry Leadership Training',
                'description': 'Specialized training for emerging leaders in Christian ministry, covering leadership principles and church administration.',
                'duration': '3 Months',
                'order': 4
            },
            {
                'title': 'Biblical Theology & Doctrine',
                'description': 'Deep theological study covering systematic theology, biblical interpretation, and core Christian doctrines.',
                'duration': '5 Months',
                'order': 5
            },
            {
                'title': 'Pastoral Care & Counseling',
                'description': 'Training in pastoral care, biblical counseling, and spiritual guidance for ministry workers.',
                'duration': '3 Months',
                'order': 6
            },
            {
                'title': 'Mission & Evangelism',
                'description': 'Comprehensive missions training covering evangelism, cross-cultural ministry, and church planting strategies.',
                'duration': '4 Months',
                'order': 7
            }
        ]
        
        for course_data in courses_data:
            existing_course = Course.query.filter_by(title=course_data['title']).first()
            if not existing_course:
                course = Course(
                    id=str(uuid.uuid4()),
                    title=course_data['title'],
                    description=course_data['description'],
                    duration=course_data['duration'],
                    order=course_data['order'],
                    is_active=True
                )
                db.session.add(course)
                print(f"✅ Created course: {course_data['title']}")
        
        # Commit all changes
        db.session.commit()
        print("\n🎉 Database initialization completed successfully!")
        print("\nLogin Credentials:")
        print("Admin: admin@seedsowers.org / admin123")
        print("Student: student@example.com / student123")
        print("\nYou can now start the application with: python app.py")

if __name__ == '__main__':
    init_database()
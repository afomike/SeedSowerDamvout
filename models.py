from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

# Initialize SQLAlchemy - will be connected to app later
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # For simple auth
    role = db.Column(db.String(50), default='student', nullable=False)  # student, admin, super_admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    progress = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('CourseSubmission', 
                                foreign_keys='CourseSubmission.user_id',
                                backref='student', lazy=True, cascade='all, delete-orphan')
    reviewed_submissions = db.relationship('CourseSubmission',
                                         foreign_keys='CourseSubmission.reviewed_by',
                                         backref='reviewer', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email or "Unknown User"

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.String(100), nullable=True)  # e.g. "4 Months"
    order = db.Column(db.Integer, nullable=False)  # for sequential progression
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    files = db.relationship('CourseFile', backref='course', lazy=True, cascade='all, delete-orphan')
    user_progress = db.relationship('UserProgress', backref='course', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('CourseSubmission', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'

class CourseFile(db.Model):
    __tablename__ = 'course_files'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.Enum('audio', 'video', 'pdf', name='file_type'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # in bytes
    duration = db.Column(db.String(50), nullable=True)  # for audio/video files
    order = db.Column(db.Integer, nullable=False)  # order within course
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_progress = db.relationship('UserProgress', backref='file', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CourseFile {self.title}>'
    
    def get_file_icon(self):
        icons = {
            'audio': '🎵',
            'video': '🎥',
            'pdf': '📄'
        }
        return icons.get(self.file_type, '📁')

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    file_id = db.Column(db.String(36), db.ForeignKey('course_files.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<UserProgress {self.user_id}:{self.file_id}>'

class CourseSubmission(db.Model):
    __tablename__ = 'course_submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='submission_status'), 
                      default='pending', nullable=False)
    reviewed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    review_comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<CourseSubmission {self.file_name}>'
    
    def get_status_badge_class(self):
        status_classes = {
            'pending': 'badge-warning',
            'approved': 'badge-success',
            'rejected': 'badge-danger'
        }
        return status_classes.get(self.status, 'badge-secondary')

# Session storage for Flask sessions (equivalent to sessions table)
class SessionStorage(db.Model):
    __tablename__ = 'sessions'
    
    sid = db.Column(db.String(255), primary_key=True)
    sess = db.Column(db.JSON, nullable=False)
    expire = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<Session {self.sid}>'
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_migrate import Migrate
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import uuid
from datetime import datetime
import json

# Load environment variables
load_dotenv()


# Initialize Flask app
app = Flask(__name__)

# Secret key (use environment variable in production)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '3bddf28f82ab46379585757481788c6c0a2876c1051f4e94')

# Database connection (make sure password is properly URL-encoded)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:afo%40%401234@localhost/seedsowers_db'
)

# SQLAlchemy settings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload settings
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Import models and initialize database
from models import db, User, Course, CourseFile, UserProgress, CourseSubmission

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload directories with organized structure
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'course-files'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'submissions'), exist_ok=True)

# Create organized subdirectories for different file types
file_types = ['pdf', 'audio', 'video', 'image']
for file_type in file_types:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'course-files', 'organized', file_type), exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Basic routes - will expand these
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    courses = Course.query.filter_by(is_active=True).order_by(Course.order).all()
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    completed_courses = CourseSubmission.query.filter_by(
        user_id=current_user.id, 
        status='approved'
    ).all()
    
    return render_template('dashboard.html', 
                         courses=courses, 
                         user_progress=user_progress,
                         completed_courses=completed_courses)

@app.route('/courses')
@login_required
def courses():
    courses = Course.query.filter_by(is_active=True).order_by(Course.order).all()
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    completed_courses = CourseSubmission.query.filter_by(
        user_id=current_user.id, 
        status='approved'
    ).all()
    
    return render_template('courses.html', 
                         courses=courses, 
                         user_progress=user_progress,
                         completed_courses=completed_courses)

@app.route('/course/<course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    files = CourseFile.query.filter_by(course_id=course_id).order_by(CourseFile.order).all()
    user_progress = UserProgress.query.filter_by(
        user_id=current_user.id, 
        course_id=course_id
    ).all()
    
    return render_template('course_detail.html', 
                         course=course, 
                         files=files, 
                         user_progress=user_progress)

@app.route('/submissions')
@login_required
def submissions():
    user_submissions = CourseSubmission.query.filter_by(user_id=current_user.id).all()
    courses = Course.query.filter_by(is_active=True).order_by(Course.order).all()
    
    return render_template('submissions.html', 
                         submissions=user_submissions, 
                         courses=courses)

@app.route('/admin')
@login_required
def admin():
    if current_user.role not in ['admin', 'super_admin']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get admin statistics
    total_users = User.query.count()
    total_courses = Course.query.count()
    pending_submissions = CourseSubmission.query.filter_by(status='pending').count()
    total_submissions = CourseSubmission.query.count()
    
    stats = {
        'total_users': total_users,
        'total_courses': total_courses,
        'pending_submissions': pending_submissions,
        'total_submissions': total_submissions
    }
    
    return render_template('admin.html', stats=stats)

# API Routes for progress tracking
@app.route('/api/mark-complete', methods=['POST'])
@login_required
def mark_file_complete():
    data = request.get_json()
    course_id = data.get('course_id')
    file_id = data.get('file_id')
    
    if not course_id or not file_id:
        return jsonify({'error': 'Course ID and File ID are required'}), 400
    
    # Check if already completed
    existing = UserProgress.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        file_id=file_id
    ).first()
    
    if existing:
        return jsonify({'message': 'Already completed'}), 200
    
    # Mark as completed
    progress = UserProgress(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        course_id=course_id,
        file_id=file_id
    )
    
    db.session.add(progress)
    db.session.commit()
    
    return jsonify({'message': 'File marked as completed'}), 200

@app.route('/api/progress')
@login_required
def get_user_progress():
    progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': p.id,
        'course_id': p.course_id,
        'file_id': p.file_id,
        'completed_at': p.completed_at.isoformat()
    } for p in progress])

@app.route('/api/progress/completed-courses')
@login_required
def get_completed_courses():
    # Get approved submissions (completed courses)
    completed = CourseSubmission.query.filter_by(
        user_id=current_user.id,
        status='approved'
    ).all()
    
    return jsonify([s.course_id for s in completed])

# Course submission API
@app.route('/api/submit-report', methods=['POST'])
@login_required
def submit_course_report():
    course_id = request.form.get('course_id')
    comments = request.form.get('comments', '')
    
    if 'submission_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('submissions'))
    
    file = request.files['submission_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('submissions'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', filename)
        
        # Ensure submissions directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        # Create submission record
        submission = CourseSubmission(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            course_id=course_id,
            file_path=file_path,
            file_name=filename,
            file_size=os.path.getsize(file_path),
            comments=comments
        )
        
        db.session.add(submission)
        db.session.commit()
        
        flash('Report submitted successfully for review', 'success')
    else:
        flash('Invalid file type. Please upload PDF, DOC, DOCX, or TXT files only.', 'error')
    
    return redirect(url_for('submissions'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin API Routes
@app.route('/api/admin/stats')
@login_required
def admin_stats():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    stats = {
        'total_users': User.query.count(),
        'total_courses': Course.query.count(),
        'pending_submissions': CourseSubmission.query.filter_by(status='pending').count(),
        'total_submissions': CourseSubmission.query.count()
    }
    
    return jsonify(stats)

@app.route('/api/admin/courses', methods=['GET'])
@login_required
def get_admin_courses():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    courses = Course.query.order_by(Course.order).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'duration': c.duration,
        'order': c.order,
        'is_active': c.is_active,
        'created_at': c.created_at.isoformat()
    } for c in courses])

@app.route('/api/admin/courses', methods=['POST'])
@login_required
def create_course():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    course = Course(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data['description'],
        duration=data['duration'],
        order=data['order'],
        is_active=data.get('is_active', True)
    )
    
    db.session.add(course)
    db.session.commit()
    
    return jsonify({'message': 'Course created successfully', 'id': course.id}), 201

@app.route('/api/admin/courses/<course_id>/files', methods=['POST'])
@login_required
def upload_course_file(course_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    title = request.form.get('title')
    description = request.form.get('description', '')
    file_type = request.form.get('fileType')
    order = int(request.form.get('order', 1))
    duration = request.form.get('duration', '')
    
    if file and allowed_course_file(file.filename):
        # Get course details for organized folder structure
        course = Course.query.get_or_404(course_id)
        
        # Create organized folder structure: course-files/course-id/file-type/
        course_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'course-files', course_id)
        type_folder = os.path.join(course_folder, file_type)
        
        # Ensure organized directory structure exists
        os.makedirs(type_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(type_folder, filename)
        
        file.save(file_path)
        
        # Create course file record
        course_file = CourseFile(
            id=str(uuid.uuid4()),
            course_id=course_id,
            title=title,
            description=description,
            file_type=file_type,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            duration=duration,
            order=order
        )
        
        db.session.add(course_file)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully', 
            'id': course_file.id,
            'organized_path': f"course-files/{course_id}/{file_type}/{filename}"
        }), 201
    else:
        return jsonify({'error': 'Invalid file type'}), 400

def allowed_course_file(filename):
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt',  # Documents
        'mp3', 'wav', 'ogg', 'aac', 'm4a',  # Audio
        'mp4', 'avi', 'mov', 'mkv', 'webm',  # Video
        'jpg', 'jpeg', 'png', 'gif', 'bmp'  # Images
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type_from_extension(filename):
    """Automatically determine file type based on extension"""
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if extension in ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt']:
        return 'pdf'
    elif extension in ['mp3', 'wav', 'ogg', 'aac', 'm4a']:
        return 'audio'
    elif extension in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        return 'video'
    elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return 'image'
    else:
        return 'pdf'  # default fallback

@app.route('/api/admin/users')
@login_required
def get_admin_users():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'role': u.role,
        'is_active': u.is_active,
        'created_at': u.created_at.isoformat()
    } for u in users])

@app.route('/api/admin/users/<user_id>/status', methods=['PUT'])
@login_required
def update_user_status(user_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    is_active = data.get('is_active')
    
    user = User.query.get_or_404(user_id)
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'User status updated successfully'})

@app.route('/api/admin/submissions/pending')
@login_required
def get_pending_submissions():
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    submissions = db.session.query(CourseSubmission, User, Course).join(
        User, CourseSubmission.user_id == User.id
    ).join(
        Course, CourseSubmission.course_id == Course.id
    ).filter(CourseSubmission.status == 'pending').all()
    
    return jsonify([{
        'id': s.CourseSubmission.id,
        'file_name': s.CourseSubmission.file_name,
        'course_title': s.Course.title,
        'student_name': f"{s.User.first_name} {s.User.last_name}",
        'submitted_at': s.CourseSubmission.submitted_at.isoformat(),
        'comments': s.CourseSubmission.comments
    } for s in submissions])

@app.route('/api/admin/submissions/<submission_id>/review', methods=['PUT'])
@login_required
def review_submission(submission_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    status = data.get('status')  # 'approved' or 'rejected'
    review_comments = data.get('review_comments', '')
    
    submission = CourseSubmission.query.get_or_404(submission_id)
    submission.status = status
    submission.review_comments = review_comments
    submission.reviewed_by = current_user.id
    submission.reviewed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': f'Submission {status} successfully'})

# Course API Routes
@app.route('/api/courses')
@login_required
def get_courses():
    courses = Course.query.filter_by(is_active=True).order_by(Course.order).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'duration': c.duration,
        'order': c.order,
        'is_active': c.is_active
    } for c in courses])

@app.route('/api/courses/<course_id>')
@login_required
def get_course(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify({
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'duration': course.duration,
        'order': course.order,
        'is_active': course.is_active
    })

@app.route('/api/courses/<course_id>/files')
@login_required
def get_course_files(course_id):
    files = CourseFile.query.filter_by(course_id=course_id).order_by(CourseFile.order).all()
    return jsonify([{
        'id': f.id,
        'title': f.title,
        'description': f.description,
        'file_type': f.file_type,
        'file_path': f.file_path,
        'file_size': f.file_size,
        'duration': f.duration,
        'order': f.order
    } for f in files])

@app.route('/api/submissions')
@login_required
def get_user_submissions():
    submissions = CourseSubmission.query.filter_by(user_id=current_user.id).order_by(CourseSubmission.submitted_at.desc()).all()
    return jsonify([{
        'id': s.id,
        'course_id': s.course_id,
        'file_name': s.file_name,
        'file_path': s.file_path,
        'file_size': s.file_size,
        'comments': s.comments,
        'status': s.status,
        'review_comments': s.review_comments,
        'submitted_at': s.submitted_at.isoformat(),
        'reviewed_at': s.reviewed_at.isoformat() if s.reviewed_at else None
    } for s in submissions])

# Admin course file management routes
@app.route('/api/admin/courses/<course_id>/files')
@login_required
def get_course_files_admin(course_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    files = CourseFile.query.filter_by(course_id=course_id).order_by(CourseFile.order).all()
    return jsonify([{
        'id': f.id,
        'title': f.title,
        'description': f.description,
        'file_type': f.file_type,
        'file_path': f.file_path,
        'file_size': f.file_size,
        'duration': f.duration,
        'order': f.order,
        'created_at': f.created_at.isoformat()
    } for f in files])

@app.route('/api/admin/courses/<course_id>/files/<file_id>', methods=['DELETE'])
@login_required
def delete_course_file(course_id, file_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    course_file = CourseFile.query.get_or_404(file_id)
    
    # Delete physical file
    try:
        if os.path.exists(course_file.file_path):
            os.remove(course_file.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete database record
    db.session.delete(course_file)
    db.session.commit()
    
    return jsonify({'message': 'File deleted successfully'})

@app.route('/api/admin/courses/<course_id>/files/<file_id>', methods=['PUT'])
@login_required
def update_course_file(course_id, file_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    course_file = CourseFile.query.get_or_404(file_id)
    
    course_file.title = data.get('title', course_file.title)
    course_file.description = data.get('description', course_file.description)
    course_file.duration = data.get('duration', course_file.duration)
    course_file.order = data.get('order', course_file.order)
    
    db.session.commit()
    
    return jsonify({'message': 'File updated successfully'})

@app.route('/api/admin/organize-files/<course_id>')
@login_required
def organize_course_files(course_id):
    if current_user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    course = Course.query.get_or_404(course_id)
    files = CourseFile.query.filter_by(course_id=course_id).all()
    
    organized_count = 0
    for file in files:
        # Check if file is already in organized structure
        if f'course-files/{course_id}/' not in file.file_path:
            # Create new organized path
            file_extension = file.file_path.split('.')[-1]
            new_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.title)}.{file_extension}"
            new_path = os.path.join(
                app.config['UPLOAD_FOLDER'], 
                'course-files', 
                course_id, 
                file.file_type, 
                new_filename
            )
            
            # Create directory structure
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # Move file if it exists
            if os.path.exists(file.file_path):
                os.rename(file.file_path, new_path)
                file.file_path = new_path
                organized_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'Organized {organized_count} files',
        'organized_count': organized_count
    })

# File serving route with organized structure support
@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/course-files/<course_id>/<file_type>/<filename>')
@login_required
def serve_organized_file(course_id, file_type, filename):
    """Serve files from organized folder structure"""
    file_path = os.path.join('course-files', course_id, file_type)
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], file_path), filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Run on port 5001 since 5000 is used by the Node.js server
    app.run(host='0.0.0.0', port=5001, debug=True)
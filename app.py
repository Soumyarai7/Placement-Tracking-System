import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, StudentProfile, Company

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-development' # Change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup Uploads
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'zip', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_initial_data():
    if User.query.filter_by(username='admin').first() is None:
        # Create Admin
        admin_user = User(username='admin', password=generate_password_hash('admin123', method='pbkdf2:sha256'), role='admin')
        db.session.add(admin_user)
        
        # Create Sample Student
        student_user = User(username='student1', password=generate_password_hash('student123', method='pbkdf2:sha256'), role='student')
        db.session.add(student_user)
        db.session.commit() # Commit to get student_user.id
        
        student_profile = StudentProfile(user_id=student_user.id, full_name='John Doe', department='Computer Science', cgpa=8.5)
        db.session.add(student_profile)
        
        # Create another Sample Student
        student_user2 = User(username='student2', password=generate_password_hash('student123', method='pbkdf2:sha256'), role='student')
        db.session.add(student_user2)
        db.session.commit()
        
        student_profile2 = StudentProfile(user_id=student_user2.id, full_name='Jane Smith', department='Information Technology', cgpa=9.1)
        db.session.add(student_profile2)
        
        db.session.commit()
        print("Initial data created.")

with app.app_context():
    db.create_all()
    create_initial_data()


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'error')
        else:
            new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'), role=role)
            db.session.add(new_user)
            db.session.commit()
            
            if role == 'student':
                full_name = request.form.get('full_name')
                department = request.form.get('department')
                cgpa = request.form.get('cgpa')
                new_profile = StudentProfile(user_id=new_user.id, full_name=full_name, department=department, cgpa=float(cgpa))
                db.session.add(new_profile)
                db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    companies = Company.query.all()
    return render_template('student_dashboard.html', user=current_user, profile=current_user.student_profile, companies=companies)

@app.route('/student/enroll_company', methods=['POST'])
@login_required
def enroll_company():
    if current_user.role != 'student':
        return redirect(url_for('index'))
        
    company_id = request.form.get('company_id')
    if company_id:
        profile = current_user.student_profile
        profile.enrolled_company_id = int(company_id)
        db.session.commit()
        flash('Successfully enrolled in the company!', 'success')
    else:
        flash('Please select a valid company.', 'error')
        
    return redirect(url_for('student_dashboard'))

@app.route('/student/upload_cv', methods=['POST'])
@login_required
def upload_cv():
    if current_user.role != 'student':
        return redirect(url_for('index'))
        
    if 'cv' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['cv']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('student_dashboard'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{current_user.id}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        profile = current_user.student_profile
        profile.cv_filename = unique_filename
        db.session.commit()
        
        flash('File successfully uploaded', 'success')
        return redirect(url_for('student_dashboard'))
    else:
        flash('Allowed file types are pdf, doc, docx, zip, jpg, jpeg, png', 'error')
        return redirect(url_for('student_dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    students = StudentProfile.query.all()
    companies = Company.query.all()
    return render_template('admin_dashboard.html', students=students, companies=companies)

@app.route('/admin/add_company', methods=['POST'])
@login_required
def add_company():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
        
    company_name = request.form.get('name')
    company_desc = request.form.get('description')
    
    if company_name:
        existing = Company.query.filter_by(name=company_name).first()
        if existing:
            flash('Company already exists.', 'error')
        else:
            new_company = Company(name=company_name, description=company_desc)
            db.session.add(new_company)
            db.session.commit()
            flash('Company added successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_shortlist/<int:student_id>', methods=['POST'])
@login_required
def toggle_shortlist(student_id):
    if current_user.role != 'admin':
        return {'success': False, 'message': 'Unauthorized'}, 403
        
    student = StudentProfile.query.get_or_404(student_id)
    student.is_shortlisted = not student.is_shortlisted
    db.session.commit()
    
    return {'success': True, 'is_shortlisted': student.is_shortlisted}

@app.route('/uploads/<name>')
@login_required
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

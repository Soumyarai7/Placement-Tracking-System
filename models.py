from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'admin' or 'student'
    
    # Relationship to student profile if role is 'student'
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(150), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    cv_filename = db.Column(db.String(255), nullable=True) # Path to uploaded CV/file
    is_shortlisted = db.Column(db.Boolean, default=False)
    enrolled_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Relationship to Company
    company = db.relationship('Company', backref='enrolled_students')

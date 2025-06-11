# models.py - FIXED VERSION
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

# Import db from app module - this fixes the circular import
db = SQLAlchemy()

class UserRole(enum.Enum):
    ENGINEER = "engineer"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.ENGINEER, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Engineer-specific fields
    engineer_id = db.Column(db.String(100), unique=True)
    department = db.Column(db.String(100))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_engineer(self):
        return self.role == UserRole.ENGINEER
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'engineer_id': self.engineer_id,
            'department': self.department,
            'is_active': self.is_active
        }

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    engineer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    questions = db.Column(db.JSON, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    points = db.Column(db.Integer, default=120)
    is_active = db.Column(db.Boolean, default=True)
    assigned_by_admin = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships - using string references to avoid circular imports
    engineer = db.relationship('User', foreign_keys=[engineer_id], backref='assignments')
    admin = db.relationship('User', foreign_keys=[assigned_by_admin])
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'topic': self.topic,
            'engineer_username': self.engineer.username if self.engineer else None,
            'created_date': self.created_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'points': self.points,
            'question_count': len(self.questions) if self.questions else 0
        }

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.String(100), db.ForeignKey('assignments.id'), nullable=False)
    engineer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answers = db.Column(db.JSON, nullable=False)
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='submitted')
    
    # Evaluation results
    overall_score = db.Column(db.Float)
    grade_letter = db.Column(db.String(2))
    evaluation_results = db.Column(db.JSON)
    
    # Admin grading
    admin_grade = db.Column(db.String(2))
    admin_feedback = db.Column(db.Text)
    graded_by_admin = db.Column(db.Integer, db.ForeignKey('users.id'))
    graded_date = db.Column(db.DateTime)
    is_grade_released = db.Column(db.Boolean, default=False)
    
    # Relationships
    assignment = db.relationship('Assignment', backref='submissions')
    engineer = db.relationship('User', foreign_keys=[engineer_id], backref='submissions')
    grader = db.relationship('User', foreign_keys=[graded_by_admin])
    
    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'engineer_id', name='unique_submission'),
    )
    
    def to_dict(self, include_evaluation=False):
        data = {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'assignment_title': self.assignment.title if self.assignment else None,
            'engineer_username': self.engineer.username if self.engineer else None,
            'submitted_date': self.submitted_date.isoformat(),
            'status': self.status,
            'admin_grade': self.admin_grade,
            'admin_feedback': self.admin_feedback,
            'is_grade_released': self.is_grade_released
        }
        
        if include_evaluation:
            data.update({
                'overall_score': self.overall_score,
                'grade_letter': self.grade_letter,
                'evaluation_results': self.evaluation_results
            })
        
        return data

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notifications')

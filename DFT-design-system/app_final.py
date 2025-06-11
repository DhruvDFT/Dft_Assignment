# app.py - Physical Design Interview System Flask Application
# Complete deployable application with database models

import os
import random
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user
from enum import Enum
import logging

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pd_interviews.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Experience Level Enum
class ExperienceLevel(Enum):
    JUNIOR = "3-5 years"
    SENIOR = "5-8 years"
    EXPERT = "8+ years"

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    experience_years = db.Column(db.Integer, default=3)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assignments = db.relationship('Assignment', backref='engineer', lazy=True)

class Assignment(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    engineer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON string
    due_date = db.Column(db.DateTime, nullable=False)
    points = db.Column(db.Integer, default=150)
    status = db.Column(db.String(20), default='pending')
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# Login manager loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Question Data
PHYSICAL_DESIGN_TOPICS_3PLUS = {
    "floorplanning": {
        "title": "Physical Design: Floorplanning (3+ Years Experience)",
        "questions": [
            "You have a 5mm x 5mm die with 4 hard macros (each 1mm x 0.8mm) and need to achieve 70% utilization. Describe your macro placement strategy considering timing and power delivery.",
            "Your design has setup timing violations on paths crossing from left to right. The floorplan has macros placed randomly. How would you reorganize the floorplan to improve timing?",
            "You're working with a design that has 2 voltage domains (0.9V core, 1.2V IO). Explain how you would plan the floorplan to minimize level shifter count and power grid complexity.",
            "During floorplan, you notice routing congestion in the center region. What are 3 specific techniques you would use to reduce congestion without major timing impact?",
            "Your design has 3 clock domains running at 800MHz, 400MHz, and 100MHz. How would you approach floorplanning to minimize clock tree power and skew?",
            "You need to place 8 memory instances in your design. What factors would you consider for their placement?",
            "Your floorplan review shows IR drop violations in certain regions. Describe your approach to fix this.",
            "You're told to reduce die area by 10% while maintaining timing. What floorplan modifications would you make?",
            "Your design has mixed-signal blocks that need isolation from digital switching noise. How would you handle their placement?",
            "During early floorplan, how would you estimate routing congestion?",
            "You have a hierarchical design with 3 major blocks. Explain your approach to partition-level floorplanning.",
            "Your design requires scan chains for testing. How does DFT impact your floorplan decisions?",
            "You're working on a power-sensitive design. Describe floorplan techniques to enable effective power gating.",
            "Your floorplan needs to accommodate late ECOs. How would you plan for flexibility?",
            "Explain your methodology for floorplan validation."
        ]
    },
    "placement": {
        "title": "Physical Design: Placement Optimization (3+ Years Experience)",
        "questions": [
            "Your placement run shows timing violations on 20 critical paths with negative slack up to -50ps. Describe your systematic approach to fix these violations.",
            "You're seeing routing congestion hotspots after placement in 2-3 regions. What placement adjustments would you make?",
            "Your design has high-fanout nets (>500 fanout) causing placement issues. How would you handle these nets?",
            "Compare global placement vs detailed placement - what specific problems does each solve?",
            "Your placement shows leakage power higher than target. What placement techniques would you use to reduce power?",
            "You have a multi-voltage design with voltage islands. Describe your placement strategy for cells near domain boundaries.",
            "Your timing report shows hold violations scattered across the design. How would you address this through placement?",
            "During placement, you notice that certain instances are creating long routes. What tools help identify and fix such issues?",
            "Your design has clock gating cells. Explain their optimal placement strategy.",
            "You're working with a design that has both high-performance and low-power modes. How does this affect placement?",
            "Your placement review shows uneven cell density distribution. Why is this problematic?",
            "Describe your approach to placement optimization for designs with multiple timing corners.",
            "Your design has redundant logic for reliability. How would you place redundant instances?",
            "You need to optimize placement for both area and timing. Describe the trade-offs.",
            "Explain how placement impacts signal integrity."
        ]
    },
    "routing": {
        "title": "Physical Design: Routing and Timing Closure (3+ Years Experience)",
        "questions": [
            "After global routing, you have 500 DRC violations. Describe your systematic approach to resolve these.",
            "Your design has 10 differential pairs for high-speed signals. Explain your routing strategy.",
            "You're seeing timing degradation after detailed routing. What causes this and how would you recover?",
            "Your router is struggling with congestion leading to routing non-completion. What techniques would you use?",
            "Describe your approach to power/ground routing.",
            "Your design has specific layer constraints. How does this impact your routing strategy?",
            "You have crosstalk violations on critical nets. Explain your routing techniques to minimize crosstalk.",
            "Your clock nets require special routing with controlled skew. Describe clock routing methodology.",
            "During routing, some nets are showing electromigration violations. How would you address this?",
            "You need to route in a design with double patterning constraints. Explain the challenges.",
            "Your design has antenna violations after routing. What causes these?",
            "Describe your ECO routing strategy.",
            "Your timing closure requires specific net delays. How do you control routing parasitics?",
            "You're working with advanced technology nodes (7nm/5nm). What routing challenges are specific to these?",
            "Explain your routing verification methodology."
        ]
    }
}

# Question Manager Class
class QuestionManager:
    def __init__(self):
        self.topics = PHYSICAL_DESIGN_TOPICS_3PLUS
        
    def get_questions_for_topic(self, topic, count=15):
        """Get random questions for a topic"""
        if topic in self.topics:
            all_questions = self.topics[topic]["questions"]
            return random.sample(all_questions, min(count, len(all_questions)))
        return []
    
    def get_mixed_questions(self, topic, experience_years):
        """Get questions mixed by difficulty based on experience"""
        questions = self.get_questions_for_topic(topic, 15)
        
        # Add difficulty-based bonus questions for higher experience
        if experience_years >= 5:
            questions.append(f"Design a complete {topic} methodology for a 100M gate design. Include automation and quality checks.")
        if experience_years >= 8:
            questions.append(f"You're the {topic} lead for a new 5nm project. Define the complete flow and team structure.")
            
        return questions[:15]  # Ensure exactly 15 questions

# Assignment Manager
class AssignmentManager:
    def __init__(self):
        self.question_manager = QuestionManager()
    
    def create_assignment(self, engineer_id, topic, experience_years=3):
        """Create a new assignment"""
        questions = self.question_manager.get_mixed_questions(topic, experience_years)
        
        # Determine difficulty parameters
        if experience_years >= 8:
            points = 200
            due_days = 21
            difficulty = "Expert"
        elif experience_years >= 5:
            points = 175
            due_days = 14
            difficulty = "Advanced"
        else:
            points = 150
            due_days = 10
            difficulty = "Intermediate"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        assignment_id = f"PD_{topic.upper()}_{engineer_id}_{timestamp}"
        
        assignment = Assignment(
            id=assignment_id,
            title=f"{topic.title()} Assessment - {difficulty} Level",
            topic=topic,
            engineer_id=engineer_id,
            questions=json.dumps(questions),
            due_date=datetime.now() + timedelta(days=due_days),
            points=points
        )
        
        return assignment
    
    def should_refresh_assignment(self, assignment):
        """Check if assignment should be refreshed"""
        if not assignment.due_date:
            return False
            
        days_since_due = (datetime.now() - assignment.due_date).days
        return days_since_due >= 7  # Refresh 7 days after deadline
    
    def refresh_assignments(self):
        """Auto-refresh expired assignments"""
        try:
            expired_assignments = Assignment.query.filter(
                Assignment.due_date < datetime.now() - timedelta(days=7),
                Assignment.status != 'refreshed'
            ).all()
            
            refreshed_count = 0
            
            for assignment in expired_assignments:
                # Check if engineer already has recent assignment
                recent = Assignment.query.filter(
                    Assignment.engineer_id == assignment.engineer_id,
                    Assignment.topic == assignment.topic,
                    Assignment.created_date > datetime.now() - timedelta(days=30)
                ).filter(Assignment.id != assignment.id).first()
                
                if not recent:
                    engineer = User.query.get(assignment.engineer_id)
                    new_assignment = self.create_assignment(
                        engineer.id,
                        assignment.topic,
                        engineer.experience_years
                    )
                    db.session.add(new_assignment)
                    
                    # Create notification
                    notification = Notification(
                        user_id=engineer.id,
                        title=f"New {assignment.topic.title()} Assignment Available",
                        message=f"A refreshed assignment with updated questions is ready."
                    )
                    db.session.add(notification)
                    
                    # Mark old assignment as refreshed
                    assignment.status = 'refreshed'
                    refreshed_count += 1
            
            if refreshed_count > 0:
                db.session.commit()
                
            return refreshed_count
            
        except Exception as e:
            logger.error(f"Auto-refresh error: {e}")
            db.session.rollback()
            return 0

# Initialize managers
assignment_manager = AssignmentManager()

# Routes
@app.route('/')
def index():
    """Home page"""
    return jsonify({
        "message": "Physical Design Interview System API",
        "version": "1.0",
        "endpoints": {
            "POST /api/assignments/create": "Create new assignment",
            "GET /api/assignments": "List all assignments",
            "POST /api/assignments/refresh": "Auto-refresh assignments",
            "GET /api/analytics": "Get assignment analytics"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/assignments/create', methods=['POST'])
def create_assignment():
    """Create assignment endpoint"""
    try:
        data = request.get_json()
        engineer_id = data.get('engineer_id', 1)
        topic = data.get('topic', 'floorplanning')
        experience_years = data.get('experience_years', 3)
        
        # Validate topic
        if topic not in ['floorplanning', 'placement', 'routing']:
            return jsonify({'error': 'Invalid topic'}), 400
        
        # Create assignment
        assignment = assignment_manager.create_assignment(
            engineer_id,
            topic,
            experience_years
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'topic': assignment.topic,
                'due_date': assignment.due_date.isoformat(),
                'points': assignment.points,
                'num_questions': len(json.loads(assignment.questions))
            }
        })
        
    except Exception as e:
        logger.error(f"Create assignment error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/assignments', methods=['GET'])
def list_assignments():
    """List assignments endpoint"""
    try:
        engineer_id = request.args.get('engineer_id')
        topic = request.args.get('topic')
        status = request.args.get('status')
        
        query = Assignment.query
        
        if engineer_id:
            query = query.filter_by(engineer_id=engineer_id)
        if topic:
            query = query.filter_by(topic=topic)
        if status:
            query = query.filter_by(status=status)
            
        assignments = query.order_by(Assignment.created_date.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'assignments': [{
                'id': a.id,
                'title': a.title,
                'topic': a.topic,
                'engineer_id': a.engineer_id,
                'due_date': a.due_date.isoformat(),
                'points': a.points,
                'status': a.status,
                'created_date': a.created_date.isoformat()
            } for a in assignments],
            'count': len(assignments)
        })
        
    except Exception as e:
        logger.error(f"List assignments error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/assignments/refresh', methods=['POST'])
def refresh_assignments():
    """Auto-refresh assignments endpoint"""
    try:
        refreshed_count = assignment_manager.refresh_assignments()
        
        return jsonify({
            'success': True,
            'message': f'Auto-refreshed {refreshed_count} assignments',
            'refreshed_count': refreshed_count
        })
        
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics endpoint"""
    try:
        # Basic analytics
        total_assignments = Assignment.query.count()
        by_status = db.session.query(
            Assignment.status, 
            db.func.count(Assignment.id)
        ).group_by(Assignment.status).all()
        
        by_topic = db.session.query(
            Assignment.topic,
            db.func.count(Assignment.id)
        ).group_by(Assignment.topic).all()
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_assignments': total_assignments,
                'by_status': dict(by_status),
                'by_topic': dict(by_topic),
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/<topic>', methods=['GET'])
def get_sample_questions(topic):
    """Get sample questions for a topic"""
    try:
        if topic not in ['floorplanning', 'placement', 'routing']:
            return jsonify({'error': 'Invalid topic'}), 400
            
        qm = QuestionManager()
        questions = qm.get_questions_for_topic(topic, 5)
        
        return jsonify({
            'success': True,
            'topic': topic,
            'sample_questions': questions
        })
        
    except Exception as e:
        logger.error(f"Get questions error: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Create tables and run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from models import User, Assignment, Submission, Notification, UserRole
from evaluator import TechnicalEvaluator, evaluate_technical_submission
from functools import wraps
import datetime
import random

# Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def engineer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_engineer():
            return jsonify({'error': 'Engineer access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Topic Questions
TOPICS = {
    "floorplanning": [
        "Design a floorplan for a 10mm x 10mm chip with 8 macro blocks. Discuss your placement strategy.",
        "Given a design with 3 power domains, explain how you would approach floorplanning to minimize power grid IR drop.",
        "Compare different floorplanning approaches for a CPU design. Justify your choice considering area, timing, and power trade-offs.",
        "How would you handle floorplanning for a design with 2 voltage domains and level shifters?",
        "Explain the impact of package constraints on your floorplanning decisions for a BGA package.",
        "Design a hierarchical floorplan for a large design with multiple hierarchy levels.",
        "How would you optimize floorplan for thermal management in a high-power design?",
        "Describe your approach to floorplanning for DFT considerations with scan chains.",
        "How would you handle floorplanning for mixed-signal designs with analog blocks?",
        "Explain pin assignment strategy for your floorplan considering I/O constraints.",
        "How would you validate your floorplan meets all timing, power, and area requirements?",
        "Describe congestion analysis and mitigation strategies in your floorplan.",
        "How would you handle floorplanning for designs with hard and soft macros?",
        "Explain your methodology for floorplan optimization iterations and convergence criteria.",
        "How would you approach floorplanning for low-power designs with power gating?"
    ],
    "placement": [
        "Explain the impact of placement on timing for a design running at 1500 MHz. Discuss congestion vs timing trade-offs.",
        "Design has 80% utilization and 10 routing layers. Analyze placement strategies to minimize routing congestion.",
        "Compare global placement vs detailed placement algorithms. When would you choose one over the other?",
        "Given timing violations on setup paths, propose placement-based solutions without changing the netlist.",
        "How would you handle placement optimization for a design with 4 clock domains and 50 ps skew budget?",
        "Describe placement strategies for power optimization considering 20% leakage reduction.",
        "How would you approach placement for designs with 5 timing corners and PVT variations?",
        "Explain placement techniques for minimizing crosstalk in 7nm technology.",
        "How would you handle placement of analog blocks in a mixed-signal design with noise constraints?",
        "Describe your approach to placement optimization for routability in congested designs.",
        "How would you handle placement for designs with multiple voltage islands and level shifters?",
        "Explain placement strategies for clock tree synthesis optimization.",
        "How would you approach placement for DFT structures and scan chain optimization?",
        "Describe placement techniques for power grid optimization and IR drop minimization.",
        "How would you validate placement quality and predict routing success?"
    ],
    "routing": [
        "Design has 2500 DRC violations after initial routing. Propose a systematic approach to resolve them.",
        "Explain routing challenges in 7nm technology. How do you handle double patterning constraints?",
        "Compare different routing algorithms (maze routing, line-search, A*) for a design with high congestion.",
        "Design requires 12 metal layers for routing. Justify your layer assignment strategy for different net types.",
        "How would you handle routing for 25 differential pairs with 100 ohm impedance?",
        "Describe your approach to power grid routing for 2.0 mA/um current density requirements.",
        "How would you optimize routing for crosstalk reduction in noisy environments?",
        "Explain routing strategies for clock networks with 30 ps skew targets.",
        "How would you handle routing in double patterning technology with coloring constraints?",
        "Describe routing techniques for high-speed signals with 5 GHz switching.",
        "How would you approach routing for mixed-signal designs with analog isolation requirements?",
        "Explain routing optimization for manufacturability and yield improvement.",
        "How would you handle routing congestion resolution without timing degradation?",
        "Describe routing strategies for power optimization and electromigration prevention.",
        "How would you validate routing quality and ensure timing closure?"
    ]
}

def register_routes(app):
    """Register all routes with the Flask app"""
    
    # Landing page
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('engineer_dashboard'))
        return redirect(url_for('login'))
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('engineer_dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please provide both username and password.', 'error')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password) and user.is_active:
                user.last_login = datetime.datetime.utcnow()
                db.session.commit()
                login_user(user, remember=True)
                
                if user.is_admin():
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('engineer_dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('login'))
    
    # Admin routes
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        stats = {
            'total_engineers': User.query.filter_by(role=UserRole.ENGINEER, is_active=True).count(),
            'total_submissions': Submission.query.count(),
            'pending_grading': Submission.query.filter(Submission.admin_grade.is_(None)).count(),
            'graded_submissions': Submission.query.filter(
                Submission.admin_grade.isnot(None),
                Submission.is_grade_released == True
            ).count()
        }
        
        recent_activities = []
        recent_submissions = Submission.query.order_by(Submission.submitted_date.desc()).limit(5).all()
        
        for submission in recent_submissions:
            recent_activities.append({
                'title': 'New Submission',
                'description': f'{submission.engineer.username} submitted {submission.assignment.title}',
                'timestamp': submission.submitted_date.strftime('%Y-%m-%d %H:%M')
            })
        
        return render_template('admin_dashboard.html', **stats, recent_activities=recent_activities)
    
    @app.route('/admin/submissions')
    @login_required
    @admin_required
    def admin_submissions():
        page = request.args.get('page', 1, type=int)
        submissions = Submission.query.order_by(Submission.submitted_date.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        engineers = User.query.filter_by(role=UserRole.ENGINEER).all()
        topics = list(TOPICS.keys())
        
        return render_template('admin_submissions.html', 
                             submissions=submissions, 
                             engineers=engineers, 
                             topics=topics)
    
    @app.route('/admin/submission/<int:submission_id>')
    @login_required
    @admin_required
    def admin_submission_details(submission_id):
        submission = Submission.query.get_or_404(submission_id)
        return render_template('admin_submission_details.html', submission=submission)
    
    @app.route('/admin/submission/<int:submission_id>/grade', methods=['POST'])
    @login_required
    @admin_required
    def grade_submission(submission_id):
        submission = Submission.query.get_or_404(submission_id)
        data = request.get_json()
        
        admin_grade = data.get('admin_grade')
        admin_feedback = data.get('admin_feedback', '')
        release_grade = data.get('release_grade', False)
        
        if admin_grade not in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']:
            return jsonify({'error': 'Invalid grade'}), 400
        
        try:
            submission.admin_grade = admin_grade
            submission.admin_feedback = admin_feedback
            submission.graded_by_admin = current_user.id
            submission.graded_date = datetime.datetime.utcnow()
            submission.is_grade_released = release_grade
            submission.status = 'graded'
            
            db.session.commit()
            
            if release_grade:
                # Send notification
                notification = Notification(
                    user_id=submission.engineer_id,
                    title=f"Grade Released - {submission.assignment.title}",
                    message=f"Your grade ({admin_grade}) has been released.",
                    type='success'
                )
                db.session.add(notification)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Grade {admin_grade} assigned' + (' and released' if release_grade else '')
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/submission/<int:submission_id>/release-grade', methods=['POST'])
    @login_required
    @admin_required
    def release_grade(submission_id):
        submission = Submission.query.get_or_404(submission_id)
        
        if not submission.admin_grade:
            return jsonify({'error': 'No grade assigned yet'}), 400
        
        try:
            submission.is_grade_released = True
            db.session.commit()
            
            # Send notification
            notification = Notification(
                user_id=submission.engineer_id,
                title=f"Grade Released - {submission.assignment.title}",
                message=f"Your grade ({submission.admin_grade}) has been released.",
                type='success'
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Grade released to engineer'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    # Engineer routes
    @app.route('/engineer/dashboard')
    @login_required
    @engineer_required
    def engineer_dashboard():
        assignments = Assignment.query.filter_by(engineer_id=current_user.id).all()
        submissions = Submission.query.filter_by(
            engineer_id=current_user.id,
            is_grade_released=True
        ).all()
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).order_by(Notification.created_date.desc()).limit(5).all()
        
        return render_template('engineer_dashboard.html',
                             assignments=assignments,
                             submissions=submissions,
                             notifications=notifications)
    
    @app.route('/engineer/assignment/<assignment_id>')
    @login_required
    @engineer_required
    def engineer_assignment(assignment_id):
        assignment = Assignment.query.filter_by(
            id=assignment_id,
            engineer_id=current_user.id
        ).first_or_404()
        
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            engineer_id=current_user.id
        ).first()
        
        return render_template('engineer_assignment.html',
                             assignment=assignment,
                             submission=submission)
    
    # API routes
    @app.route('/api/submit', methods=['POST'])
    @login_required
    @engineer_required
    @limiter.limit("3 per hour")
    def api_submit():
        data = request.get_json()
        assignment_id = data.get('assignment_id')
        answers = data.get('answers', [])
        
        # Verify ownership
        assignment = Assignment.query.filter_by(
            id=assignment_id,
            engineer_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Check existing submission
        existing = Submission.query.filter_by(
            assignment_id=assignment_id,
            engineer_id=current_user.id
        ).first()
        
        if existing:
            return jsonify({'error': 'Already submitted'}), 409
        
        try:
            # Create submission
            submission = Submission(
                assignment_id=assignment_id,
                engineer_id=current_user.id,
                answers=answers
            )
            
            db.session.add(submission)
            db.session.commit()
            
            # Evaluate submission
            try:
                evaluation_results = evaluate_technical_submission(answers, assignment.topic)
                submission.overall_score = evaluation_results['overall_score']
                submission.grade_letter = evaluation_results['grade_letter']
                submission.evaluation_results = evaluation_results
                submission.status = 'evaluated'
                db.session.commit()
            except Exception as e:
                print(f"Evaluation failed: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Assignment submitted successfully!',
                'submission_id': submission.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Submission failed'}), 500
    
    # Create demo assignments
    @app.route('/api/create-demo-assignments')
    @login_required
    @admin_required
    def create_demo_assignments():
        """Create demo assignments for testing"""
        try:
            engineers = User.query.filter_by(role=UserRole.ENGINEER).all()
            
            for engineer in engineers:
                # Check if engineer already has assignments
                existing = Assignment.query.filter_by(engineer_id=engineer.id).first()
                if existing:
                    continue
                
                # Create one assignment per topic
                for topic in TOPICS.keys():
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    assignment_id = f"PD_{topic.upper()}_{engineer.engineer_id}_{timestamp}"
                    
                    assignment = Assignment(
                        id=assignment_id,
                        title=f"{topic.title()} Technical Assessment",
                        topic=topic,
                        engineer_id=engineer.id,
                        questions=TOPICS[topic],
                        due_date=datetime.date.today() + datetime.timedelta(days=7),
                        points=120,
                        assigned_by_admin=current_user.id
                    )
                    
                    db.session.add(assignment)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Demo assignments created'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'system': 'Physical Design Assignment System v2.0'
        })

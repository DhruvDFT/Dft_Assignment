# app.py - Ultra-Safe PD Interview System for Railway
import os
import hashlib
from datetime import datetime, timedelta

# Import Flask with explicit error handling
try:
    from flask import Flask, request, redirect, session
except ImportError as e:
    print(f"Flask import error: {e}")
    exit(1)

# Create app with minimal config
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pd-interview-secret-2024')

# Disable ALL logging completely to prevent Railway errors
import sys
import logging

# Multiple layers of logging disabling
logging.disable(logging.CRITICAL)
logging.getLogger().disabled = True
logging.getLogger('werkzeug').disabled = True

# Disable Flask's built-in logger
if hasattr(app, 'logger'):
    app.logger.disabled = True
    app.logger.setLevel(logging.CRITICAL)

# Redirect stderr to prevent any log output
class NullWriter:
    def write(self, txt): pass
    def flush(self): pass

sys.stderr = NullWriter()

# Safe password functions
def hash_password(password):
    try:
        return hashlib.sha256(str(password).encode('utf-8')).hexdigest()
    except Exception:
        return None

def check_password(hashed, password):
    try:
        return hashed == hashlib.sha256(str(password).encode('utf-8')).hexdigest()
    except Exception:
        return False

# Global storage - simple and safe
users = {}
assignments = {}
assignment_counter = 0

# Enhanced questions database
QUESTIONS_DB = {
    "floorplanning": [
        {
            "text": "You have a 5mm x 5mm die with 4 hard macros (each 1mm x 0.8mm) and need to achieve 70% utilization. Describe your macro placement strategy considering timing and power delivery.",
            "level": "intermediate",
            "points": 10,
            "keywords": ["macro", "timing", "power", "utilization", "placement"]
        },
        {
            "text": "Your design has setup timing violations on paths crossing from left to right. The floorplan has macros placed randomly. How would you reorganize the floorplan to improve timing?",
            "level": "intermediate", 
            "points": 10,
            "keywords": ["timing", "violations", "floorplan", "macros", "reorganize"]
        },
        {
            "text": "During floorplan, you notice routing congestion in the center region. What are 3 specific techniques you would use to reduce congestion without major timing impact?",
            "level": "beginner",
            "points": 10,
            "keywords": ["congestion", "routing", "techniques", "timing"]
        }
    ],
    "placement": [
        {
            "text": "Your placement run shows timing violations on 20 critical paths with negative slack up to -50ps. Describe your systematic approach to fix these violations.",
            "level": "intermediate",
            "points": 10,
            "keywords": ["timing", "violations", "slack", "critical", "systematic"]
        },
        {
            "text": "You're seeing routing congestion hotspots after placement in 2-3 regions. What placement adjustments would you make to improve routability?",
            "level": "intermediate",
            "points": 10,
            "keywords": ["congestion", "placement", "routability", "adjustments"]
        },
        {
            "text": "Your design has high-fanout nets (>500 fanout) causing placement issues. How would you handle these nets during placement optimization?",
            "level": "advanced",
            "points": 10,
            "keywords": ["fanout", "nets", "placement", "optimization"]
        }
    ],
    "routing": [
        {
            "text": "After global routing, you have 500 DRC violations (spacing, via, width). Describe your systematic approach to resolve these violations efficiently.",
            "level": "intermediate",
            "points": 10,
            "keywords": ["DRC", "violations", "spacing", "systematic"]
        },
        {
            "text": "Your design has 10 differential pairs for high-speed signals. Explain your routing strategy to maintain 100-ohm impedance and minimize skew.",
            "level": "advanced",
            "points": 10,
            "keywords": ["differential", "impedance", "skew", "routing"]
        },
        {
            "text": "You're seeing timing degradation after detailed routing compared to placement timing. What causes this and how would you recover the timing?",
            "level": "intermediate",
            "points": 10,
            "keywords": ["timing", "degradation", "routing", "placement"]
        }
    ]
}

def safe_get_questions(engineer_id, topic):
    """Safely get questions based on engineer experience"""
    try:
        engineer = users.get(engineer_id, {})
        experience = engineer.get('experience_years', 3)
        
        questions = QUESTIONS_DB.get(topic, [])
        if not questions:
            return []
        
        # Simple experience-based selection
        if experience <= 2:
            # Junior engineers get easier questions
            selected = [q for q in questions if q.get('level') in ['beginner', 'intermediate']]
        elif experience <= 4:
            # Mid-level gets mixed
            selected = questions
        else:
            # Senior gets harder questions
            selected = [q for q in questions if q.get('level') in ['intermediate', 'advanced']]
        
        return selected[:3] if selected else questions[:3]
    except Exception:
        # Fallback to first 3 questions
        return QUESTIONS_DB.get(topic, [])[:3]

def safe_calculate_score(answer, question):
    """Safe AI scoring calculation"""
    try:
        if not answer or not isinstance(answer, str):
            return 0
        
        answer_lower = answer.lower()
        keywords = question.get('keywords', [])
        
        score = 0
        for keyword in keywords:
            if str(keyword).lower() in answer_lower:
                score += 1.5
        
        # Length bonus
        word_count = len(answer.split())
        if word_count > 30:
            score += 1
        if word_count > 60:
            score += 1
        
        return min(round(score, 1), 10)
    except Exception:
        return 0

def safe_create_assignment(engineer_id, topic):
    """Safely create assignment"""
    global assignment_counter
    
    try:
        if engineer_id not in users or topic not in QUESTIONS_DB:
            return None
        
        assignment_counter += 1
        assignment_id = f"PD_{topic.upper()}_{engineer_id}_{assignment_counter}"
        
        questions = safe_get_questions(engineer_id, topic)
        if not questions:
            return None
        
        assignment = {
            'id': assignment_id,
            'engineer_id': engineer_id,
            'topic': topic,
            'questions': questions,
            'answers': {},
            'scores': {},
            'status': 'pending',
            'created_date': datetime.now().isoformat(),
            'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
            'total_score': None,
            'max_score': sum(q.get('points', 10) for q in questions),
            'scored_by': None
        }
        
        assignments[assignment_id] = assignment
        return assignment
    except Exception:
        return None

def safe_init_users():
    """Safely initialize users"""
    try:
        # Admin user
        admin_password = hash_password('Vibhuaya@3006')
        if admin_password:
            users['admin'] = {
                'id': 'admin',
                'username': 'admin',
                'password': admin_password,
                'is_admin': True,
                'experience_years': 5
            }
        
        # Engineer users with varied experience
        engineers_data = [
            {'id': 'eng001', 'exp': 2},
            {'id': 'eng002', 'exp': 4}, 
            {'id': 'eng003', 'exp': 6},
            {'id': 'eng004', 'exp': 3},
            {'id': 'eng005', 'exp': 5}
        ]
        
        eng_password = hash_password('password123')
        if eng_password:
            for eng in engineers_data:
                users[eng['id']] = {
                    'id': eng['id'],
                    'username': eng['id'],
                    'password': eng_password,
                    'is_admin': False,
                    'experience_years': eng['exp']
                }
    except Exception:
        # Fallback minimal users
        users['admin'] = {
            'id': 'admin',
            'username': 'admin', 
            'password': 'hashed_admin_pass',
            'is_admin': True,
            'experience_years': 5
        }

# Safe HTML generation functions
def generate_login_html(error=None):
    """Generate safe login HTML"""
    error_html = ''
    if error:
        error_html = f'<div class="error">❌ {str(error)}</div>'
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PD Assessment System</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            width: 400px;
            max-width: 90%;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 28px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 30px;
        }}
        .form-group {{ margin-bottom: 20px; }}
        label {{
            display: block;
            color: #374151;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        input {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }}
        input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        .btn {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }}
        .info {{
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            border: 1px solid #0ea5e9;
            border-radius: 12px;
            padding: 16px;
            margin: 20px 0;
            text-align: center;
        }}
        .info h4 {{ color: #0c4a6e; margin-bottom: 10px; }}
        .info p {{ color: #0369a1; font-size: 14px; margin: 5px 0; }}
        .error {{
            background: #fee2e2;
            border: 1px solid #f87171;
            color: #dc2626;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .features {{
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
        .tag {{
            display: inline-block;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 11px;
            margin: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ PD Assessment</h1>
        {error_html}
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autocomplete="username">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required autocomplete="current-password">
            </div>
            <button type="submit" class="btn">Sign In</button>
        </form>
        <div class="info">
            <h4>🔑 Test Credentials</h4>
            <p><strong>Engineers:</strong> eng001, eng002, eng003, eng004, eng005</p>
            <p><strong>Password:</strong> password123</p>
        </div>
        <div class="features">
            <span class="tag">🤖 Smart Scoring</span>
            <span class="tag">📊 Analytics</span>
            <span class="tag">🎯 Adaptive</span>
            <span class="tag">💡 Enhanced</span>
        </div>
    </div>
</body>
</html>'''

# Routes with comprehensive error handling
@app.route('/')
def home():
    try:
        if 'user_id' in session:
            if session.get('is_admin'):
                return redirect('/admin')
            else:
                return redirect('/student')
        return redirect('/login')
    except Exception:
        return redirect('/login')

@app.route('/health')
def health():
    try:
        return 'OK', 200
    except Exception:
        return 'ERROR', 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        error = None
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if username and password:
                user = users.get(username)
                if user and check_password(user.get('password'), password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['is_admin'] = user.get('is_admin', False)
                    
                    if user.get('is_admin'):
                        return redirect('/admin')
                    else:
                        return redirect('/student')
                else:
                    error = 'Invalid credentials'
            else:
                error = 'Please enter both username and password'
        
        return generate_login_html(error)
    except Exception as e:
        return generate_login_html('System error occurred')

@app.route('/logout')
def logout():
    try:
        session.clear()
        return redirect('/login')
    except Exception:
        return redirect('/login')

@app.route('/admin')
def admin_dashboard():
    try:
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect('/login')
        
        engineers = [u for u in users.values() if not u.get('is_admin')]
        all_assignments = list(assignments.values())
        submitted = [a for a in all_assignments if a.get('status') == 'submitted']
        
        # Generate engineer options
        engineer_options = ''
        for eng in engineers:
            exp_years = eng.get('experience_years', 0)
            if exp_years <= 2:
                level = 'Junior'
            elif exp_years <= 4:
                level = 'Mid'
            else:
                level = 'Senior'
            engineer_options += f'<option value="{eng["id"]}">{eng["username"]} ({level} - {exp_years}y)</option>'
        
        # Generate submitted assignments
        submitted_html = ''
        if submitted:
            for a in submitted:
                engineer = users.get(a['engineer_id'], {})
                submitted_html += f'''
                <div class="assignment-item">
                    <strong>{a["topic"].title()} - {a["engineer_id"]}</strong><br>
                    <small>Experience: {engineer.get("experience_years", 0)} years | Questions: {len(a.get("questions", []))} | Max: {a.get("max_score", 30)}</small><br>
                    <a href="/admin/review/{a["id"]}" class="btn btn-success" style="margin-top: 8px;">Review & Score</a>
                </div>'''
        else:
            submitted_html = '<div class="empty">📭 No pending reviews</div>'
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #1e293b;
        }}
        .header {{
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            color: white;
            padding: 20px 0;
        }}
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }}
        .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            text-align: center;
        }}
        .stat-number {{ font-size: 28px; font-weight: 700; color: #1e40af; margin-bottom: 6px; }}
        .stat-label {{ color: #64748b; font-size: 14px; }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 24px;
        }}
        .card-header {{
            background: #f8fafc;
            padding: 20px 24px;
            border-bottom: 1px solid #e2e8f0;
            border-radius: 12px 12px 0 0;
        }}
        .card-body {{ padding: 24px; }}
        .form-row {{ display: flex; gap: 12px; align-items: end; flex-wrap: wrap; }}
        .form-group {{ flex: 1; min-width: 150px; }}
        label {{ display: block; margin-bottom: 6px; color: #374151; font-weight: 500; }}
        select {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: white;
        }}
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }}
        .btn-primary {{ background: #3b82f6; color: white; }}
        .btn-success {{ background: #10b981; color: white; }}
        .assignment-item {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }}
        .logout-btn {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            text-decoration: none;
        }}
        .empty {{ text-align: center; padding: 40px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>⚡ Admin Dashboard</h1>
            <div>
                <span>👨‍💼 {session['username']}</span>
                <a href="/logout" class="logout-btn">Logout</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(engineers)}</div>
                <div class="stat-label">Engineers</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(all_assignments)}</div>
                <div class="stat-label">Assignments</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(submitted)}</div>
                <div class="stat-label">Pending</div>
            </div>
            <div class="stat">
                <div class="stat-number">9</div>
                <div class="stat-label">Smart Questions</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>🎯 Create Smart Assessment</h2>
            </div>
            <div class="card-body">
                <form method="POST" action="/admin/create">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Engineer</label>
                            <select name="engineer_id" required>
                                <option value="">Select...</option>
                                {engineer_options}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Topic</label>
                            <select name="topic" required>
                                <option value="">Select...</option>
                                <option value="floorplanning">🏗️ Floorplanning</option>
                                <option value="placement">📍 Placement</option>
                                <option value="routing">🛤️ Routing</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <button type="submit" class="btn btn-primary">Create</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>📋 Submitted Assessments</h2>
            </div>
            <div class="card-body">
                {submitted_html}
            </div>
        </div>
    </div>
</body>
</html>'''
    except Exception:
        return redirect('/login')

@app.route('/admin/create', methods=['POST'])
def admin_create():
    try:
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect('/login')
        
        engineer_id = request.form.get('engineer_id', '').strip()
        topic = request.form.get('topic', '').strip()
        
        if engineer_id and topic:
            safe_create_assignment(engineer_id, topic)
        
        return redirect('/admin')
    except Exception:
        return redirect('/admin')

@app.route('/admin/review/<assignment_id>', methods=['GET', 'POST'])
def admin_review(assignment_id):
    try:
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect('/login')
        
        assignment = assignments.get(assignment_id)
        if not assignment:
            return redirect('/admin')
        
        if request.method == 'POST':
            total_score = 0
            questions = assignment.get('questions', [])
            
            for i in range(len(questions)):
                score_str = request.form.get(f'score_{i}', '0')
                try:
                    score = float(score_str)
                    total_score += score
                except (ValueError, TypeError):
                    total_score += 0
            
            assignment['total_score'] = round(total_score, 1)
            assignment['status'] = 'published'
            assignment['scored_by'] = session.get('username', 'admin')
            assignment['scored_date'] = datetime.now().isoformat()
            
            return redirect('/admin')
        
        # Generate review page
        questions = assignment.get('questions', [])
        questions_html = ''
        
        for i, question in enumerate(questions):
            answer = assignment.get('answers', {}).get(str(i), 'No answer provided')
            auto_score = safe_calculate_score(answer, question)
            
            questions_html += f'''
            <div class="card">
                <div class="card-header">
                    <h4>Question {i+1} of {len(questions)}</h4>
                    <small>Level: {question.get("level", "intermediate").title()} | Points: {question.get("points", 10)}</small>
                </div>
                <div class="card-body">
                    <div class="question">
                        <strong>Q:</strong> {question.get("text", "Question not available")}
                    </div>
                    <h5>📝 Answer:</h5>
                    <div class="answer">{answer}</div>
                    <div class="ai-info">
                        <strong>🤖 AI Score:</strong> {auto_score}/10
                    </div>
                    <div class="scoring">
                        <label><strong>👨‍🏫 Your Score:</strong></label>
                        <input type="number" name="score_{i}" min="0" max="{question.get("points", 10)}" 
                               value="{auto_score}" class="score-input" required step="0.5">
                        <span>/ {question.get("points", 10)}</span>
                    </div>
                </div>
            </div>'''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Assessment</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #1e293b;
        }}
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 20px 0; }}
        .container {{ max-width: 1000px; margin: 20px auto; padding: 0 20px; }}
        .card {{
            background: white;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }}
        .card-header {{
            background: #f8fafc;
            padding: 16px 20px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .card-body {{ padding: 20px; }}
        .question {{
            background: #f1f5f9;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            border-left: 4px solid #3b82f6;
        }}
        .answer {{
            background: #fefefe;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
        }}
        .scoring {{
            background: #f8fafc;
            padding: 16px;
            border-radius: 8px;
        }}
        .score-input {{
            width: 60px;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            text-align: center;
            font-weight: 600;
        }}
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
        }}
        .btn-primary {{ background: #3b82f6; color: white; }}
        .btn-secondary {{ background: #6b7280; color: white; }}
        .submit-section {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}
        .ai-info {{
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
            <h1>📝 Review Assessment: {assignment_id}</h1>
            <p>{assignment['topic'].title()} - {assignment['engineer_id']}</p>
        </div>
    </div>
    
    <div class="container">
        <form method="POST">
            {questions_html}
            <div class="submit-section">
                <button type="submit" class="btn btn-primary">✅ Publish Final Scores</button>
                <a href="/admin" class="btn btn-secondary">← Back to Dashboard</a>
            </div>
        </form>
    </div>
</body>
</html>'''
    except Exception:
        return redirect('/admin')

@app.route('/student')
def student_dashboard():
    try:
        if 'user_id' not in session:
            return redirect('/login')
        
        user_id = session['user_id']
        user = users.get(user_id, {})
        my_assignments = [a for a in assignments.values() if a.get('engineer_id') == user_id]
        
        # Generate assignment cards
        assignments_html = ''
        if my_assignments:
            for a in my_assignments:
                status = a.get('status', 'pending')
                topic = a.get('topic', 'unknown')
                
                # Topic icon
                topic_icons = {'floorplanning': '🏗️', 'placement': '📍', 'routing': '🛤️'}
                topic_icon = topic_icons.get(topic, '📝')
                
                # Status content
                status_content = ''
                if status == 'published':
                    total_score = a.get('total_score', 0)
                    max_score = a.get('max_score', 30)
                    percentage = (total_score / max_score * 100) if max_score > 0 else 0
                    status_content = f'''
                    <div class="score-display">
                        <strong>Score: {total_score}/{max_score} ({percentage:.1f}%)</strong>
                    </div>'''
                elif status == 'submitted':
                    status_content = '<p style="text-align: center; color: #3b82f6; font-weight: 500;">⏳ Under AI analysis and admin review</p>'
                elif status == 'pending':
                    status_content = f'''
                    <a href="/student/assignment/{a['id']}" class="btn btn-primary" style="width: 100%; margin-top: 8px;">
                        🚀 Start Smart Assessment
                    </a>'''
                
                assignments_html += f'''
                <div class="assignment">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div class="assignment-title">
                            {topic_icon} {topic.title()} Assessment
                        </div>
                        <span class="status status-{status}">{status}</span>
                    </div>
                    <div class="assignment-meta">
                        <div class="meta-item">
                            <div class="meta-value">{len(a.get('questions', []))}</div>
                            <div class="meta-label">Questions</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-value">{a.get("max_score", 30)}</div>
                            <div class="meta-label">Max Score</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-value">{a.get("due_date", "")[:10]}</div>
                            <div class="meta-label">Due Date</div>
                        </div>
                    </div>
                    {status_content}
                </div>'''
        else:
            assignments_html = '''
            <div class="empty">
                <h3>📭 No Assessments Yet</h3>
                <p>Your smart assessments will appear here when created by admin.</p>
            </div>'''
        
        completed_count = len([a for a in my_assignments if a.get('status') == 'published'])
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Engineer Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #1e293b;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 20px 0;
        }}
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }}
        .header h1 {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 24px;
            font-weight: 700;
        }}
        .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        .stat-number {{ font-size: 24px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }}
        .stat-label {{ color: #64748b; font-size: 12px; text-transform: uppercase; }}
        .section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        .assignment {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            transition: all 0.3s ease;
        }}
        .assignment:hover {{ border-color: #667eea; transform: translateY(-2px); }}
        .assignment-title {{ font-size: 18px; font-weight: 600; color: #1e293b; }}
        .assignment-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 10px;
            margin: 12px 0;
            padding: 12px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            font-size: 13px;
        }}
        .meta-item {{ text-align: center; }}
        .meta-value {{ font-weight: 600; color: #1e293b; }}
        .meta-label {{ color: #64748b; font-size: 11px; text-transform: uppercase; }}
        .status {{
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-pending {{ background: #fbbf24; color: white; }}
        .status-submitted {{ background: #3b82f6; color: white; }}
        .status-published {{ background: #10b981; color: white; }}
        .btn {{
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); }}
        .logout-btn {{
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            text-decoration: none;
        }}
        .score-display {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            margin-top: 8px;
        }}
        .empty {{ text-align: center; padding: 40px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>⚡ Engineer Dashboard</h1>
            <div>
                <span>👨‍💼 {session['username']} ({user.get('experience_years', 0)} years)</span>
                <a href="/logout" class="logout-btn">Logout</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(my_assignments)}</div>
                <div class="stat-label">Assessments</div>
            </div>
            <div class="stat">
                <div class="stat-number">{completed_count}</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat">
                <div class="stat-number">{user.get('experience_years', 0)}y</div>
                <div class="stat-label">Experience</div>
            </div>
            <div class="stat">
                <div class="stat-number">🤖</div>
                <div class="stat-label">AI Enhanced</div>
            </div>
        </div>
        
        <div class="section">
            <h2 style="margin-bottom: 20px;">📚 My Smart Assessments</h2>
            {assignments_html}
        </div>
    </div>
</body>
</html>'''
    except Exception:
        return redirect('/login')

@app.route('/student/assignment/<assignment_id>', methods=['GET', 'POST'])
def student_assignment(assignment_id):
    try:
        if 'user_id' not in session:
            return redirect('/login')
        
        assignment = assignments.get(assignment_id)
        if not assignment or assignment.get('engineer_id') != session['user_id']:
            return redirect('/student')
        
        if request.method == 'POST' and assignment.get('status') == 'pending':
            answers = {}
            questions = assignment.get('questions', [])
            
            for i in range(len(questions)):
                answer = request.form.get(f'answer_{i}', '').strip()
                if answer:
                    answers[str(i)] = answer
            
            if len(answers) == len(questions):
                assignment['answers'] = answers
                assignment['status'] = 'submitted'
                assignment['submitted_date'] = datetime.now().isoformat()
            
            return redirect('/student')
        
        questions = assignment.get('questions', [])
        topic = assignment.get('topic', 'unknown')
        topic_icons = {'floorplanning': '🏗️', 'placement': '📍', 'routing': '🛤️'}
        topic_icon = topic_icons.get(topic, '📝')
        
        # Generate question cards
        questions_html = ''
        for i, question in enumerate(questions):
            level = question.get('level', 'intermediate')
            points = question.get('points', 10)
            text = question.get('text', 'Question not available')
            
            questions_html += f'''
            <div class="question-card">
                <div class="question-header">
                    <div class="question-number">Question {i+1} of {len(questions)}</div>
                    <div class="question-meta">
                        <span class="meta-badge">⚡ {level.title()}</span>
                        <span class="meta-badge">🎯 {points} pts</span>
                    </div>
                </div>
                <div class="question-text">{text}</div>
                <div>
                    <label class="answer-label">✍️ Your Answer:</label>
                    <textarea name="answer_{i}" class="answer-textarea" 
                              placeholder="Provide a detailed technical answer with examples and methodologies..." 
                              required></textarea>
                </div>
            </div>'''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic.title()} Assessment</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #1e293b;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 20px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-content {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
            text-align: center;
        }}
        .title {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .container {{ max-width: 1000px; margin: 20px auto; padding: 0 20px; }}
        .question-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        .question-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f1f5f9;
        }}
        .question-number {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
        }}
        .question-meta {{ display: flex; gap: 10px; font-size: 12px; }}
        .meta-badge {{
            background: rgba(102, 126, 234, 0.1);
            color: #4f46e5;
            padding: 4px 8px;
            border-radius: 10px;
            font-weight: 500;
        }}
        .question-text {{
            font-size: 16px;
            line-height: 1.6;
            color: #1e293b;
            margin-bottom: 20px;
            padding: 16px;
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }}
        .answer-label {{ font-weight: 600; color: #374151; margin-bottom: 8px; }}
        .answer-textarea {{
            width: 100%;
            min-height: 120px;
            padding: 16px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            background: #fefefe;
            transition: all 0.3s ease;
            resize: vertical;
        }}
        .answer-textarea:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        .submit-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
        }}
        .warning {{
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            border: 1px solid #f59e0b;
            color: #92400e;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            font-weight: 500;
        }}
        .btn {{
            padding: 14px 28px;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 0 8px;
            transition: all 0.3s ease;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3); }}
        .btn-secondary {{
            background: rgba(107, 114, 128, 0.1);
            color: #374151;
            border: 1px solid #d1d5db;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="title">{topic_icon} {topic.title()} Assessment</div>
            <p style="color: #64748b;">📊 {len(questions)} Smart Questions | 🎯 Max: {assignment.get('max_score', 30)} Points</p>
        </div>
    </div>
    
    <div class="container">
        <form method="POST">
            {questions_html}
            <div class="submit-section">
                <div class="warning">
                    ⚠️ Review all answers before submitting. You cannot edit after submission.
                </div>
                <button type="submit" class="btn btn-primary">🚀 Submit Assessment</button>
                <a href="/student" class="btn btn-secondary">← Back to Dashboard</a>
            </div>
        </form>
    </div>
</body>
</html>'''
    except Exception:
        return redirect('/student')

# Initialize the system safely
try:
    safe_init_users()
except Exception:
    pass

# Main execution
if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Startup error: {e}")
        exit(1)

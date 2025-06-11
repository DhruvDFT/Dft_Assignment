# app.py - Physical Design Interview System (3 Questions Version)
import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pd-secret-2024')

# In-memory storage
users = {}
assignments = {}
notifications = {}
assignment_counter = 0

# Initialize default users
def init_users():
    # Admin
    users['admin'] = {
        'id': 'admin',
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'is_admin': True,
        'experience_years': 3
    }
    
    # Students
    for i in range(1, 4):
        user_id = f'eng00{i}'
        users[user_id] = {
            'id': user_id,
            'username': user_id,
            'password': generate_password_hash('password123'),
            'is_admin': False,
            'experience_years': 3
        }

# 3 Questions per topic (3+ Years Experience)
QUESTIONS = {
    "floorplanning": [
        "You have a 5mm x 5mm die with 4 hard macros (each 1mm x 0.8mm) and need to achieve 70% utilization. Describe your macro placement strategy considering timing and power delivery.",
        "Your design has setup timing violations on paths crossing from left to right. The floorplan has macros placed randomly. How would you reorganize the floorplan to improve timing?",
        "During floorplan, you notice routing congestion in the center region. What are 3 specific techniques you would use to reduce congestion without major timing impact?"
    ],
    "placement": [
        "Your placement run shows timing violations on 20 critical paths with negative slack up to -50ps. Describe your systematic approach to fix these violations.",
        "You're seeing routing congestion hotspots after placement in 2-3 regions. What placement adjustments would you make to improve routability?",
        "Your design has high-fanout nets (>500 fanout) causing placement issues. How would you handle these nets during placement optimization?"
    ],
    "routing": [
        "After global routing, you have 500 DRC violations (spacing, via, width). Describe your systematic approach to resolve these violations efficiently.",
        "Your design has 10 differential pairs for high-speed signals. Explain your routing strategy to maintain 100-ohm impedance and minimize skew.",
        "You're seeing timing degradation after detailed routing compared to placement timing. What causes this and how would you recover the timing?"
    ]
}

# Keywords for auto-scoring (2 points per keyword found, max 10 per question)
ANSWER_KEYWORDS = {
    "floorplanning": {
        0: ["macro placement", "timing", "power", "utilization", "power delivery", "IR drop", "blockage", "pins", "orientation", "dataflow"],
        1: ["setup violations", "timing paths", "floorplan", "critical paths", "placement", "buffers", "repeaters", "pipeline", "hierarchy", "partition"],
        2: ["congestion", "routing", "density", "spreading", "blockages", "channels", "utilization", "cell density", "padding", "keep-out"]
    },
    "placement": {
        0: ["timing violations", "negative slack", "optimization", "critical paths", "placement", "setup", "hold", "clock", "incremental", "ECO"],
        1: ["congestion", "hotspots", "spreading", "density", "padding", "blockages", "magnet placement", "guides", "regions", "utilization"],
        2: ["high-fanout", "buffer tree", "cloning", "load splitting", "placement", "clustering", "net weights", "timing", "physical synthesis", "optimization"]
    },
    "routing": {
        0: ["DRC violations", "spacing", "via", "width", "metal", "tracks", "reroute", "ECO", "search repair", "manual fixes"],
        1: ["differential pairs", "impedance", "matching", "shielding", "spacing", "length matching", "skew", "routing", "symmetry", "guard rings"],
        2: ["timing degradation", "parasitics", "RC delay", "crosstalk", "coupling", "optimization", "layer assignment", "via optimization", "buffer", "sizing"]
    }
}

# Scoring rubric
SCORING_RUBRIC = {
    10: "Excellent - Comprehensive answer with deep understanding",
    8: "Very Good - Covers most key points with good detail",
    6: "Good - Basic understanding with some key points",
    4: "Fair - Limited understanding, missing key concepts",
    2: "Poor - Minimal understanding shown",
    0: "No answer or completely incorrect"
}

# Helper functions
def calculate_auto_score(answer, topic, question_index):
    """Calculate auto-score based on keywords"""
    if not answer:
        return 0
    
    answer_lower = answer.lower()
    keywords_found = 0
    
    if topic in ANSWER_KEYWORDS and question_index < len(ANSWER_KEYWORDS[topic]):
        keywords = ANSWER_KEYWORDS[topic][question_index]
        for keyword in keywords:
            if keyword.lower() in answer_lower:
                keywords_found += 1
    
    # 2 points per keyword, max 10 points
    return min(keywords_found * 2, 10)

def create_assignment(engineer_id, topic):
    global assignment_counter
    
    user = users.get(engineer_id)
    if not user or topic not in QUESTIONS:
        return None
    
    assignment_counter += 1
    assignment_id = f"PD_{topic.upper()}_{engineer_id}_{assignment_counter}"
    
    assignment = {
        'id': assignment_id,
        'engineer_id': engineer_id,
        'topic': topic,
        'questions': QUESTIONS[topic],
        'answers': {},
        'auto_scores': {},  # Auto-calculated scores
        'final_scores': {},  # Admin's final scores
        'status': 'pending',  # pending -> submitted -> under_review -> published
        'created_date': datetime.now().isoformat(),
        'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
        'total_score': None,
        'scored_by': None,
        'scored_date': None,
        'published_date': None
    }
    
    assignments[assignment_id] = assignment
    
    # Create notification
    if engineer_id not in notifications:
        notifications[engineer_id] = []
    
    notifications[engineer_id].append({
        'title': f'New {topic} Assignment',
        'message': f'3 questions for 3+ years experience, due in 3 days',
        'created_at': datetime.now().isoformat()
    })
    
    return assignment

# HTML Templates
def get_base_html():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PD Interview System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
            .header { background: #4CAF50; color: white; padding: 20px; }
            .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
            .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            textarea { min-height: 100px; resize: vertical; }
            button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #45a049; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; }
            .question { background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }
            .answer-box { margin-top: 10px; background: white; padding: 10px; border: 1px solid #ddd; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .badge-pending { background: #FFC107; color: #333; }
            .badge-submitted { background: #2196F3; color: white; }
            .badge-under_review { background: #FF5722; color: white; }
            .badge-published { background: #4CAF50; color: white; }
            .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
            .stat { text-align: center; }
            .stat h2 { margin: 0; color: #4CAF50; }
            .error { color: red; }
            .success { color: green; }
            .score-box { display: flex; align-items: center; gap: 20px; margin: 10px 0; }
            .auto-score { background: #e3f2fd; padding: 5px 10px; border-radius: 4px; }
            .rubric { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px; font-size: 12px; }
        </style>
    </head>
    <body>
    '''

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect('/admin')
        else:
            return redirect('/student')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            
            if user.get('is_admin'):
                return redirect('/admin')
            else:
                return redirect('/student')
        else:
            error = 'Invalid credentials'
    
    html = get_base_html() + f'''
        <div style="max-width: 400px; margin: 100px auto;">
            <div class="card">
                <h1 style="text-align: center;">Physical Design Interview System</h1>
                <p style="text-align: center; color: #666;">3 Questions per Topic (3+ Years)</p>
                <p style="background: #e3f2fd; padding: 10px; border-radius: 4px;">
                    <strong>Demo Credentials:</strong><br>
                    Admin: admin / admin123<br>
                    Student: eng001 / password123
                </p>
                {f'<p class="error">{error}</p>' if error else ''}
                <form method="POST">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit" style="width: 100%;">Login</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    engineers = [u for u in users.values() if not u.get('is_admin')]
    all_assignments = list(assignments.values())
    
    # Count assignments by status
    submitted = [a for a in all_assignments if a['status'] == 'submitted']
    under_review = [a for a in all_assignments if a['status'] == 'under_review']
    published = [a for a in all_assignments if a['status'] == 'published']
    
    html = get_base_html() + f'''
        <div class="header">
            <h1>Admin Dashboard - {session["username"]} <a href="/logout" style="float: right; color: white;">Logout</a></h1>
        </div>
        
        <div class="container">
            <div class="stats">
                <div class="stat card">
                    <h2>{len(engineers)}</h2>
                    <p>Engineers</p>
                </div>
                <div class="stat card">
                    <h2>{len(submitted)}</h2>
                    <p>Submitted</p>
                </div>
                <div class="stat card">
                    <h2>{len(under_review)}</h2>
                    <p>Under Review</p>
                </div>
                <div class="stat card">
                    <h2>{len(published)}</h2>
                    <p>Published</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Create Assignment</h2>
                <form method="POST" action="/admin/create">
                    <div class="form-group">
                        <label>Engineer</label>
                        <select name="engineer_id" required>
                            <option value="">Select...</option>
    '''
    
    for eng in engineers:
        html += f'<option value="{eng["id"]}">{eng["username"]}</option>'
    
    html += '''
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Topic</label>
                        <select name="topic" required>
                            <option value="">Select...</option>
                            <option value="floorplanning">Floorplanning</option>
                            <option value="placement">Placement</option>
                            <option value="routing">Routing</option>
                        </select>
                    </div>
                    <button type="submit">Create Assignment</button>
                </form>
            </div>
            
            <div class="card">
                <h2>Submitted Assignments (Ready for Review)</h2>
    '''
    
    if submitted:
        for a in submitted:
            html += f'''
                <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                    <h4>{a["id"]} - {a["engineer_id"]} - {a["topic"].title()}</h4>
                    <p>Submitted: All 3 answers | Auto-score calculated</p>
                    <a href="/admin/review/{a["id"]}"><button>Review & Score</button></a>
                </div>
            '''
    else:
        html += '<p>No assignments ready for review</p>'
    
    html += '''
            </div>
            
            <div class="card">
                <h2>All Assignments</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Engineer</th>
                        <th>Topic</th>
                        <th>Status</th>
                        <th>Score</th>
                        <th>Action</th>
                    </tr>
    '''
    
    for a in all_assignments[-10:]:  # Last 10
        action = ""
        if a['status'] == 'under_review':
            action = f'<a href="/admin/publish/{a["id"]}"><button>Publish</button></a>'
        elif a['status'] == 'published':
            action = "Published ✓"
            
        html += f'''
            <tr>
                <td>{a["id"]}</td>
                <td>{a["engineer_id"]}</td>
                <td>{a["topic"]}</td>
                <td><span class="badge badge-{a["status"]}">{a["status"]}</span></td>
                <td>{a.get("total_score", "-")}/30</td>
                <td>{action}</td>
            </tr>
        '''
    
    html += '''
                </table>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/admin/create', methods=['POST'])
def admin_create():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    engineer_id = request.form.get('engineer_id')
    topic = request.form.get('topic')
    
    if engineer_id and topic:
        create_assignment(engineer_id, topic)
    
    return redirect('/admin')

@app.route('/admin/review/<assignment_id>', methods=['GET', 'POST'])
def admin_review(assignment_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    assignment = assignments.get(assignment_id)
    if not assignment or assignment['status'] != 'submitted':
        return redirect('/admin')
    
    if request.method == 'POST':
        # Save final scores
        total_score = 0
        for i in range(3):  # 3 questions
            score = request.form.get(f'score_{i}', '0')
            try:
                final_score = int(score)
                assignment['final_scores'][str(i)] = final_score
                total_score += final_score
            except:
                pass
        
        assignment['total_score'] = total_score
        assignment['scored_by'] = session['username']
        assignment['scored_date'] = datetime.now().isoformat()
        assignment['status'] = 'under_review'
        
        return redirect('/admin')
    
    # Calculate auto-scores if not done
    if not assignment.get('auto_scores'):
        for i, question in enumerate(assignment['questions']):
            answer = assignment.get('answers', {}).get(str(i), '')
            assignment['auto_scores'][str(i)] = calculate_auto_score(answer, assignment['topic'], i)
    
    # Show review form
    html = get_base_html() + f'''
        <div class="header">
            <h1>Review Assignment - {assignment_id}</h1>
        </div>
        
        <div class="container">
            <div class="card">
                <h3>Engineer: {assignment["engineer_id"]} | Topic: {assignment["topic"].title()}</h3>
                
                <div class="rubric">
                    <strong>Scoring Rubric:</strong><br>
    '''
    
    for score, desc in SCORING_RUBRIC.items():
        html += f'{score}: {desc}<br>'
    
    html += '''
                </div>
                
                <form method="POST">
    '''
    
    for i, question in enumerate(assignment['questions']):
        answer = assignment.get('answers', {}).get(str(i), 'No answer provided')
        auto_score = assignment.get('auto_scores', {}).get(str(i), 0)
        
        html += f'''
            <div class="question">
                <strong>Q{i+1}:</strong> {question}
                <div class="answer-box">
                    <strong>Student's Answer:</strong><br>
                    {answer}
                </div>
                <div class="score-box">
                    <div class="auto-score">
                        Auto-score (Keywords): {auto_score}/10
                    </div>
                    <div>
                        <label>Final Score (0-10):</label>
                        <input type="number" name="score_{i}" min="0" max="10" value="{auto_score}" style="width: 60px;">
                    </div>
                </div>
            </div>
        '''
    
    html += '''
                    <button type="submit" style="margin-top: 20px;">Save Scores (Next: Publish)</button>
                    <a href="/admin"><button type="button">Cancel</button></a>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/admin/publish/<assignment_id>')
def admin_publish(assignment_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    assignment = assignments.get(assignment_id)
    if not assignment or assignment['status'] != 'under_review':
        return redirect('/admin')
    
    # Publish the assignment
    assignment['status'] = 'published'
    assignment['published_date'] = datetime.now().isoformat()
    
    # Notify student
    engineer_id = assignment['engineer_id']
    if engineer_id not in notifications:
        notifications[engineer_id] = []
    
    notifications[engineer_id].append({
        'title': f'{assignment["topic"].title()} Assignment Scored',
        'message': f'Your assignment has been evaluated. Score: {assignment["total_score"]}/30',
        'created_at': datetime.now().isoformat()
    })
    
    return redirect('/admin')

@app.route('/student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    my_assignments = [a for a in assignments.values() if a['engineer_id'] == user_id]
    my_notifications = notifications.get(user_id, [])[-5:]
    
    html = get_base_html() + f'''
        <div class="header">
            <h1>Student Dashboard - {session["username"]} <a href="/logout" style="float: right; color: white;">Logout</a></h1>
        </div>
        
        <div class="container">
    '''
    
    if my_notifications:
        html += '<div class="card"><h2>Notifications</h2>'
        for n in my_notifications:
            html += f'<p><strong>{n["title"]}</strong><br>{n["message"]}<br><small>{n["created_at"][:16]}</small></p>'
        html += '</div>'
    
    html += '<h2>My Assignments</h2>'
    
    if my_assignments:
        for a in my_assignments:
            html += f'''
                <div class="card">
                    <h3>{a["topic"].title()} Assignment 
                        <span class="badge badge-{a["status"]}">{a["status"]}</span>
                    </h3>
                    <p>Due: {a["due_date"][:10]}</p>
            '''
            
            if a['status'] == 'published':
                html += f'<p><strong>Score: {a["total_score"]}/30</strong> (Scored by: {a.get("scored_by", "Admin")})</p>'
                html += f'<a href="/student/assignment/{a["id"]}"><button>View Results</button></a>'
            elif a['status'] in ['submitted', 'under_review']:
                html += '<p>Your submission is being reviewed...</p>'
            else:
                html += f'<a href="/student/assignment/{a["id"]}"><button>Answer Questions</button></a>'
            
            html += '</div>'
    else:
        html += '<div class="card"><p>No assignments yet.</p></div>'
    
    html += '''
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/student/assignment/<assignment_id>', methods=['GET', 'POST'])
def student_assignment(assignment_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    assignment = assignments.get(assignment_id)
    if not assignment or assignment['engineer_id'] != session['user_id']:
        return redirect('/student')
    
    if request.method == 'POST' and assignment['status'] == 'pending':
        # Save answers
        answers = {}
        for i in range(3):  # 3 questions
            answer = request.form.get(f'answer_{i}', '').strip()
            if answer:
                answers[str(i)] = answer
        
        if len(answers) == 3:  # All questions answered
            assignment['answers'] = answers
            assignment['status'] = 'submitted'
            
            # Calculate auto-scores
            for i in range(3):
                answer = answers.get(str(i), '')
                assignment['auto_scores'][str(i)] = calculate_auto_score(answer, assignment['topic'], i)
        
        return redirect('/student')
    
    # Show assignment
    html = get_base_html() + f'''
        <div class="header">
            <h1>{assignment["topic"].title()} Assignment</h1>
        </div>
        
        <div class="container">
            <div class="card">
                <p>Status: <span class="badge badge-{assignment["status"]}">{assignment["status"]}</span> | Due: {assignment["due_date"][:10]}</p>
    '''
    
    if assignment['status'] == 'published':
        html += f'<p><strong>Total Score: {assignment["total_score"]}/30</strong></p>'
    
    if assignment['status'] == 'pending':
        html += '<form method="POST">'
    
    for i, question in enumerate(assignment['questions']):
        html += f'''
            <div class="question">
                <strong>Q{i+1}:</strong> {question}
        '''
        
        if assignment['status'] == 'pending':
            html += f'''
                <div class="answer-box">
                    <textarea name="answer_{i}" placeholder="Type your answer here..." required></textarea>
                </div>
            '''
        elif assignment['status'] in ['submitted', 'under_review', 'published']:
            answer = assignment.get('answers', {}).get(str(i), '')
            html += f'''
                <div class="answer-box">
                    <strong>Your Answer:</strong><br>
                    {answer}
                </div>
            '''
            
            if assignment['status'] == 'published':
                final_score = assignment.get('final_scores', {}).get(str(i), 0)
                html += f'<p><strong>Score: {final_score}/10</strong></p>'
        
        html += '</div>'
    
    if assignment['status'] == 'pending':
        html += '''
            <button type="submit" style="margin-top: 20px;">Submit All Answers</button>
            </form>
        '''
    
    html += '''
                <a href="/student"><button type="button">Back to Dashboard</button></a>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'users': len(users), 'assignments': len(assignments)})

# Initialize
init_users()

# Create demo assignment
if len(assignments) == 0:
    create_assignment('eng001', 'floorplanning')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

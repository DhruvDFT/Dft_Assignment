# app.py - Physical Design Interview System with Login
import os
import random
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pd-interview-secret-key-2024')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage
users_db = {}
assignments_db = {}
notifications_db = {}
assignment_counter = 0

# Initialize default users
def init_users():
    """Initialize default admin and student users"""
    # Admin user
    users_db['admin'] = {
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'role': 'admin',
        'email': 'admin@pdis.com',
        'experience_years': 10
    }
    
    # Student users
    for i in range(1, 4):
        username = f'eng00{i}'
        users_db[username] = {
            'username': username,
            'password': generate_password_hash('password123'),
            'role': 'student',
            'email': f'{username}@pdis.com',
            'experience_years': 3 + i
        }
    logger.info("Default users initialized")

# Complete Physical Design Questions (3+ Years)
PD_QUESTIONS = {
    "floorplanning": [
        "You have a 5mm x 5mm die with 4 hard macros (each 1mm x 0.8mm) and need to achieve 70% utilization. Describe your macro placement strategy considering timing and power delivery.",
        "Your design has setup timing violations on paths crossing from left to right. The floorplan has macros placed randomly. How would you reorganize the floorplan to improve timing?",
        "You're working with a design that has 2 voltage domains (0.9V core, 1.2V IO). Explain how you would plan the floorplan to minimize level shifter count and power grid complexity.",
        "During floorplan, you notice routing congestion in the center region. What are 3 specific techniques you would use to reduce congestion without major timing impact?",
        "Your design has 3 clock domains running at 800MHz, 400MHz, and 100MHz. How would you approach floorplanning to minimize clock tree power and skew?",
        "You need to place 8 memory instances in your design. What factors would you consider for their placement, and how would you verify the floorplan quality?",
        "Your floorplan review shows IR drop violations in certain regions. Describe your approach to fix this through floorplan changes and power grid improvements.",
        "You're told to reduce die area by 10% while maintaining timing. What floorplan modifications would you make and what risks would you monitor?",
        "Your design has mixed-signal blocks that need isolation from digital switching noise. How would you handle their placement and what guard techniques would you use?",
        "During early floorplan, how would you estimate routing congestion and what tools/techniques help predict routability issues?",
        "You have a hierarchical design with 3 major blocks. Explain your approach to partition-level floorplanning and interface planning between blocks.",
        "Your design requires scan chains for testing. How does DFT impact your floorplan decisions and what considerations are important for scan routing?",
        "You're working on a power-sensitive design. Describe floorplan techniques to enable effective power gating and retention strategies.",
        "Your floorplan needs to accommodate late ECOs (Engineering Change Orders). How would you plan for flexibility and what areas would you keep available?",
        "Explain your methodology for floorplan validation - what checks would you run and what metrics indicate a good floorplan ready for placement?"
    ],
    "placement": [
        "Your placement run shows timing violations on 20 critical paths with negative slack up to -50ps. Describe your systematic approach to fix these violations.",
        "You're seeing routing congestion hotspots after placement in 2-3 regions. What placement adjustments would you make to improve routability?",
        "Your design has high-fanout nets (>500 fanout) causing placement issues. How would you handle these nets during placement optimization?",
        "Compare global placement vs detailed placement - what specific problems does each solve and when would you iterate between them?",
        "Your placement shows leakage power higher than target. What placement techniques would you use to reduce power while maintaining timing?",
        "You have a multi-voltage design with voltage islands. Describe your placement strategy for cells near domain boundaries and level shifter placement.",
        "Your timing report shows hold violations scattered across the design. How would you address this through placement without affecting setup timing?",
        "During placement, you notice that certain instances are creating long routes. What tools and techniques help identify and fix such placement issues?",
        "Your design has clock gating cells. Explain their optimal placement strategy and impact on both power and timing.",
        "You're working with a design that has both high-performance and low-power modes. How does this affect your placement strategy?",
        "Your placement review shows uneven cell density distribution. Why is this problematic and how would you achieve better density distribution?",
        "Describe your approach to placement optimization for designs with multiple timing corners (SS, FF, TT). How do you ensure all corners meet timing?",
        "Your design has redundant logic for reliability. How would you place redundant instances to avoid common-mode failures?",
        "You need to optimize placement for both area and timing. Describe the trade-offs and how you would balance these competing requirements.",
        "Explain how placement impacts signal integrity. What placement techniques help minimize crosstalk and noise issues?"
    ],
    "routing": [
        "After global routing, you have 500 DRC violations (spacing, via, width). Describe your systematic approach to resolve these violations efficiently.",
        "Your design has 10 differential pairs for high-speed signals. Explain your routing strategy to maintain 100-ohm impedance and minimize skew.",
        "You're seeing timing degradation after detailed routing compared to placement timing. What causes this and how would you recover the timing?",
        "Your router is struggling with congestion in certain regions leading to routing non-completion. What techniques would you use to achieve 100% routing?",
        "Describe your approach to power/ground routing. How do you ensure adequate current carrying capacity and low IR drop?",
        "Your design has specific layer constraints (e.g., no routing on M1 except for local connections). How does this impact your routing strategy?",
        "You have crosstalk violations on critical nets. Explain your routing techniques to minimize crosstalk and meet noise requirements.",
        "Your clock nets require special routing with controlled skew. Describe clock routing methodology and skew optimization techniques.",
        "During routing, some nets are showing electromigration violations. How would you address current density issues through routing changes?",
        "You need to route in a design with double patterning constraints. Explain the challenges and your approach to handle decomposition issues.",
        "Your design has antenna violations after routing. What causes these and what routing techniques help prevent antenna issues?",
        "Describe your ECO (Engineering Change Order) routing strategy. How do you minimize disruption to existing clean routing?",
        "Your timing closure requires specific net delays. How do you control routing parasitics to meet timing targets?",
        "You're working with advanced technology nodes (7nm/5nm). What routing challenges are specific to these nodes and how do you address them?",
        "Explain your routing verification methodology. What checks ensure your routing is manufacturable and reliable?"
    ]
}

# Helper Functions
def create_assignment(engineer_id, topic):
    """Create a new assignment"""
    global assignment_counter
    
    if topic not in PD_QUESTIONS:
        return None
    
    user = users_db.get(engineer_id)
    if not user:
        return None
    
    experience = user.get('experience_years', 3)
    
    # Get all 15 questions for the topic
    questions = PD_QUESTIONS[topic]
    
    # Determine parameters based on experience
    if experience >= 8:
        difficulty = "Expert"
        points = 200
        due_days = 21
    elif experience >= 5:
        difficulty = "Advanced"
        points = 175
        due_days = 14
    else:
        difficulty = "Intermediate"
        points = 150
        due_days = 10
    
    assignment_counter += 1
    assignment_id = f"PD_{topic}_{engineer_id}_{assignment_counter}"
    
    assignment = {
        'id': assignment_id,
        'engineer_id': engineer_id,
        'topic': topic,
        'questions': questions,
        'points': points,
        'difficulty': difficulty,
        'status': 'pending',
        'created_date': datetime.now().isoformat(),
        'due_date': (datetime.now() + timedelta(days=due_days)).isoformat()
    }
    
    assignments_db[assignment_id] = assignment
    
    # Add notification
    add_notification(engineer_id, f"New {topic} assignment created", f"{len(questions)} questions, due in {due_days} days")
    
    return assignment

def add_notification(user_id, title, message):
    """Add a notification for a user"""
    if user_id not in notifications_db:
        notifications_db[user_id] = []
    
    notifications_db[user_id].append({
        'title': title,
        'message': message,
        'created_at': datetime.now().isoformat(),
        'read': False
    })

# Routes
@app.route('/')
def home():
    """Home page - redirect based on login status"""
    if 'user' in session:
        if session.get('role') == 'admin':
            return redirect('/admin')
        else:
            return redirect('/student')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users_db.get(username)
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['role'] = user['role']
            session['experience'] = user.get('experience_years', 3)
            
            if user['role'] == 'admin':
                return redirect('/admin')
            else:
                return redirect('/student')
        else:
            error = "Invalid credentials"
    else:
        error = None
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PD Interview System - Login</title>
        <style>
            body { font-family: Arial; background: #f0f0f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 400px; }
            h1 { text-align: center; color: #333; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #45a049; }
            .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .error { color: red; text-align: center; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🎯 Physical Design Interview System</h1>
            <div class="info">
                <strong>Demo Credentials:</strong><br>
                Admin: admin / admin123<br>
                Student: eng001 / password123
            </div>
            ''' + (f'<div class="error">{error}</div>' if error else '') + '''
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''
    
    return html if not error else html.replace('</div>', f'</div><div class="error">{error}</div>', 1)

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/login')
    
    # Get stats
    total_engineers = len([u for u in users_db.values() if u['role'] == 'student'])
    total_assignments = len(assignments_db)
    pending_assignments = len([a for a in assignments_db.values() if a['status'] == 'pending'])
    
    # Get recent assignments
    recent_assignments = sorted(assignments_db.values(), key=lambda x: x['created_date'], reverse=True)[:5]
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body {{ font-family: Arial; margin: 0; background: #f5f5f5; }}
            .header {{ background: #4CAF50; color: white; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
            .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
            .stat {{ background: white; padding: 20px; text-align: center; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stat h2 {{ margin: 0; color: #4CAF50; font-size: 36px; }}
            .stat p {{ margin: 5px 0; color: #666; }}
            button {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #45a049; }}
            select, input {{ padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #f5f5f5; }}
            .logout {{ float: right; color: white; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Admin Dashboard<a href="/logout" class="logout">Logout</a></h1>
        </div>
        
        <div class="container">
            <div class="stats">
                <div class="stat">
                    <h2>{total_engineers}</h2>
                    <p>Engineers</p>
                </div>
                <div class="stat">
                    <h2>{total_assignments}</h2>
                    <p>Total Assignments</p>
                </div>
                <div class="stat">
                    <h2>{pending_assignments}</h2>
                    <p>Pending</p>
                </div>
                <div class="stat">
                    <h2>45</h2>
                    <p>Questions (3 topics)</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Create Assignment</h2>
                <form action="/admin/create-assignment" method="POST">
                    <select name="engineer_id" required>
                        <option value="">Select Engineer</option>
    '''
    
    for username, user in users_db.items():
        if user['role'] == 'student':
            html += f'<option value="{username}">{username} ({user["experience_years"]} years)</option>'
    
    html += '''
                    </select>
                    <select name="topic" required>
                        <option value="">Select Topic</option>
                        <option value="floorplanning">Floorplanning</option>
                        <option value="placement">Placement</option>
                        <option value="routing">Routing</option>
                    </select>
                    <button type="submit">Create Assignment</button>
                </form>
            </div>
            
            <div class="card">
                <h2>Recent Assignments</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Engineer</th>
                        <th>Topic</th>
                        <th>Status</th>
                        <th>Points</th>
                    </tr>
    '''
    
    for assignment in recent_assignments:
        html += f'''
                    <tr>
                        <td>{assignment['id']}</td>
                        <td>{assignment['engineer_id']}</td>
                        <td>{assignment['topic']}</td>
                        <td>{assignment['status']}</td>
                        <td>{assignment['points']}</td>
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

@app.route('/admin/create-assignment', methods=['POST'])
def admin_create_assignment():
    """Create assignment"""
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/login')
    
    engineer_id = request.form.get('engineer_id')
    topic = request.form.get('topic')
    
    if engineer_id and topic:
        create_assignment(engineer_id, topic)
    
    return redirect('/admin')

@app.route('/student')
def student_dashboard():
    """Student dashboard"""
    if 'user' not in session:
        return redirect('/login')
    
    username = session['user']
    
    # Get student's assignments
    my_assignments = [a for a in assignments_db.values() if a['engineer_id'] == username]
    
    # Get notifications
    my_notifications = notifications_db.get(username, [])[-5:]  # Last 5
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Dashboard</title>
        <style>
            body {{ font-family: Arial; margin: 0; background: #f5f5f5; }}
            .header {{ background: #2196F3; color: white; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
            .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .assignment {{ background: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #2196F3; }}
            .question {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .badge {{ display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 12px; }}
            .pending {{ background: #FFC107; color: #333; }}
            .logout {{ float: right; color: white; text-decoration: none; }}
            h3 {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Student Dashboard - {username}<a href="/logout" class="logout">Logout</a></h1>
        </div>
        
        <div class="container">
            <div class="card">
                <h2>My Assignments</h2>
    '''
    
    if my_assignments:
        for assignment in my_assignments:
            html += f'''
                <div class="assignment">
                    <h3>{assignment['topic'].title()} Assignment <span class="badge pending">{assignment['status']}</span></h3>
                    <p>Points: {assignment['points']} | Difficulty: {assignment['difficulty']} | Due: {assignment['due_date'][:10]}</p>
                    <h4>Questions (15):</h4>
            '''
            
            for i, question in enumerate(assignment['questions'], 1):
                html += f'<div class="question"><strong>Q{i}:</strong> {question}</div>'
            
            html += '</div>'
    else:
        html += '<p>No assignments yet.</p>'
    
    html += '''
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'users': len(users_db),
        'assignments': len(assignments_db)
    })

# Initialize users on startup
init_users()

# Create some demo assignments
if len(assignments_db) == 0:
    create_assignment('eng001', 'floorplanning')
    create_assignment('eng001', 'placement')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Physical Design Interview System on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

# app.py - Minimal Working DFT System
import os
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = 'dft-secret-key'

# Global data
users = {}
assignments = {}
counter = 0

# Questions - 9 total questions, 3 per topic, unique for each engineer
QUESTIONS = {
    "scan_design": [
        "You have a design with 50,000 flip-flops and need to achieve 99% fault coverage. Describe your scan chain insertion strategy, including scan chain length optimization and timing considerations.",
        "Your scan insertion results show timing violations on scan paths with -200ps setup slack. What are the specific techniques you would use to fix scan timing without affecting functional timing?",
        "During scan insertion, you encounter 500 non-scannable flops due to X-state issues and clock domain crossings. Describe your systematic approach to make these flops scannable."
    ],
    "bist_mbist": [
        "Your design has 200 memory instances (SRAM, ROM, RF) and you need to implement MBIST. Describe your MBIST architecture, including controller placement and test algorithm selection.",
        "During MBIST implementation, you're getting 85% memory coverage instead of target 95%. What factors affect MBIST coverage and how would you improve it?",
        "Your MBIST patterns are detecting memory failures in 5% of dies. Explain your approach to analyze failure patterns and determine if they're systematic or random defects."
    ],
    "boundary_scan": [
        "Your PCB has 15 ICs with JTAG boundary scan capability. Design a JTAG chain topology considering signal integrity, debug access, and manufacturing test requirements.",
        "During boundary scan implementation, you're achieving only 60% interconnect coverage on a complex PCB. What techniques would you use to improve coverage and test quality?",
        "Your boundary scan testing reveals 20 interconnect failures between ICs. Describe your systematic approach to isolate opens, shorts, and bridging faults using boundary scan."
    ]
}

def hash_pass(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def check_pass(hashed, pwd):
    return hashed == hashlib.sha256(pwd.encode()).hexdigest()

def init_data():
    global users
    users['admin'] = {
        'id': 'admin',
        'username': 'admin',
        'password': hash_pass('Vibhuaya@3006'),
        'is_admin': True,
        'exp': 5
    }
    
    for i in range(1, 4):
        uid = f'eng00{i}'
        users[uid] = {
            'id': uid,
            'username': uid,
            'password': hash_pass('password123'),
            'is_admin': False,
            'exp': 3 + (i % 3)
        }

def create_test(eng_id, topic):
    global counter
    counter += 1
    test_id = f"DFT_{topic}_{eng_id}_{counter}"
    
    # Get engineer-specific question based on engineer ID
    eng_num = int(eng_id[-1]) - 1  # eng001->0, eng002->1, eng003->2
    question_index = eng_num % len(QUESTIONS[topic])
    
    test = {
        'id': test_id,
        'engineer_id': eng_id,
        'topic': topic,
        'questions': [QUESTIONS[topic][question_index]],  # Only one unique question per engineer
        'answers': {},
        'status': 'pending',
        'created': datetime.now().isoformat(),
        'due': (datetime.now() + timedelta(days=3)).isoformat(),
        'score': None
    }
    
    assignments[test_id] = test
    return test

@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect('/admin')
        return redirect('/student')
    return redirect('/login')

@app.route('/health')
def health():
    return 'OK'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = users.get(username)
        if user and check_pass(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            
            if user.get('is_admin'):
                return redirect('/admin')
            return redirect('/student')
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>DFT Assessment Login</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
        .box { background: rgba(255,255,255,0.95); padding: 40px; border-radius: 20px; width: 350px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        h1 { background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 16px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        .info { background: #f0f9ff; border: 1px solid #0ea5e9; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="box">
        <h1>DFT Assessment</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="info">
            <strong>Test Login:</strong><br>
            Engineers: eng001, eng002, eng003<br>
            Password: password123
        </div>
    </div>
</body>
</html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect('/login')
    
    engineers = [u for u in users.values() if not u.get('is_admin')]
    all_tests = list(assignments.values())
    pending = [a for a in all_tests if a['status'] == 'submitted']
    
    eng_options = ''
    for eng in engineers:
        eng_options += f'<option value="{eng["id"]}">{eng["username"]} ({eng["exp"]}y)</option>'
    
    pending_html = ''
    for p in pending:
        pending_html += f'''
        <div style="background: #f8fafc; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #e2e8f0;">
            <strong>{p["topic"].replace("_", " ").title()} - {p["engineer_id"]}</strong><br>
            <small>1 Question | Max: 10 points</small><br>
            <a href="/admin/review/{p["id"]}" style="background: #10b981; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 8px;">Review</a>
        </div>'''
    
    if not pending_html:
        pending_html = '<p style="text-align: center; color: #64748b; padding: 40px;">No pending reviews</p>'
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        body {{ font-family: Arial; margin: 0; background: #f8fafc; }}
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 20px 0; }}
        .container {{ max-width: 1000px; margin: 20px auto; padding: 0 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat {{ background: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-num {{ font-size: 24px; font-weight: bold; color: #1e40af; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        select, button {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }}
        button {{ background: #3b82f6; color: white; border: none; cursor: pointer; }}
        .logout {{ background: rgba(255,255,255,0.2); color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; float: right; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
            <h1>Admin Dashboard
                <a href="/logout" class="logout">Logout</a>
            </h1>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat"><div class="stat-num">{len(engineers)}</div><div>Engineers</div></div>
            <div class="stat"><div class="stat-num">{len(all_tests)}</div><div>Tests</div></div>
            <div class="stat"><div class="stat-num">{len(pending)}</div><div>Pending</div></div>
            <div class="stat"><div class="stat-num">9</div><div>Questions</div></div>
        </div>
        
        <div class="card">
            <h2>Create Test</h2>
            <form method="POST" action="/admin/create">
                <select name="engineer_id" required>
                    <option value="">Select Engineer...</option>
                    {eng_options}
                </select>
                <select name="topic" required>
                    <option value="">Select Topic...</option>
                    <option value="scan_design">Scan Design</option>
                    <option value="bist_mbist">BIST/MBIST</option>
                    <option value="boundary_scan">Boundary Scan</option>
                </select>
                <button type="submit">Create</button>
            </form>
        </div>
        
        <div class="card">
            <h2>Pending Reviews</h2>
            {pending_html}
        </div>
    </div>
</body>
</html>'''

@app.route('/admin/create', methods=['POST'])
def admin_create():
    if not session.get('is_admin'):
        return redirect('/login')
    
    eng_id = request.form.get('engineer_id')
    topic = request.form.get('topic')
    
    if eng_id and topic and topic in QUESTIONS:
        create_test(eng_id, topic)
    
    return redirect('/admin')

@app.route('/admin/review/<test_id>', methods=['GET', 'POST'])
def admin_review(test_id):
    if not session.get('is_admin'):
        return redirect('/login')
    
    test = assignments.get(test_id)
    if not test:
        return redirect('/admin')
    
    if request.method == 'POST':
        total = 0
        try:
            score = float(request.form.get('score_0', 0))
            total += score
        except:
            pass
        
        test['score'] = total
        test['status'] = 'completed'
        return redirect('/admin')
    
    questions_html = ''
    for i, q in enumerate(test['questions']):
        answer = test.get('answers', {}).get(str(i), 'No answer')
        questions_html += f'''
        <div style="background: white; border-radius: 8px; padding: 20px; margin: 15px 0;">
            <h4>Question {i+1}</h4>
            <div style="background: #f1f5f9; padding: 15px; border-radius: 6px; margin: 10px 0;">
                {q}
            </div>
            <h5>Answer:</h5>
            <div style="background: #fefefe; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; font-family: monospace; white-space: pre-wrap;">
                {answer}
            </div>
            <div style="margin: 15px 0;">
                <label><strong>Score:</strong></label>
                <input type="number" name="score_{i}" min="0" max="10" value="7" style="width: 60px; padding: 5px;">
                <span>/10</span>
            </div>
        </div>'''
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Review Test</title>
    <style>
        body {{ font-family: Arial; background: #f8fafc; margin: 0; }}
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 20px 0; }}
        .container {{ max-width: 1000px; margin: 20px auto; padding: 0 20px; }}
        button {{ background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; margin: 10px 5px; }}
        .btn-sec {{ background: #6b7280; }}
        input {{ padding: 5px; border: 1px solid #ddd; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
            <h1>Review: {test_id}</h1>
        </div>
    </div>
    
    <div class="container">
        <form method="POST">
            {questions_html}
            <div style="text-align: center; padding: 20px;">
                <button type="submit">Publish Scores</button>
                <a href="/admin"><button type="button" class="btn-sec">Back</button></a>
            </div>
        </form>
    </div>
</body>
</html>'''

@app.route('/student')
def student():
    if not session.get('user_id') or session.get('is_admin'):
        return redirect('/login')
    
    user_id = session['user_id']
    user = users.get(user_id, {})
    my_tests = [a for a in assignments.values() if a['engineer_id'] == user_id]
    
    tests_html = ''
    for t in my_tests:
        status = t['status']
        topic_display = t["topic"].replace("_", " ").title()
        if status == 'completed':
            tests_html += f'''
            <div style="background: white; border-radius: 12px; padding: 20px; margin: 15px 0;">
                <h3>{topic_display} Test</h3>
                <div style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 12px; border-radius: 8px; text-align: center;">
                    <strong>Score: {t["score"]}/10</strong>
                </div>
            </div>'''
        elif status == 'submitted':
            tests_html += f'''
            <div style="background: white; border-radius: 12px; padding: 20px; margin: 15px 0;">
                <h3>{topic_display} Test</h3>
                <p style="color: #3b82f6; text-align: center;">Under Review</p>
            </div>'''
        else:
            tests_html += f'''
            <div style="background: white; border-radius: 12px; padding: 20px; margin: 15px 0;">
                <h3>{topic_display} Test</h3>
                <a href="/student/test/{t["id"]}" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: block; text-align: center;">
                    Start Test
                </a>
            </div>'''
    
    if not tests_html:
        tests_html = '<div style="text-align: center; padding: 40px; color: #64748b;"><h3>No tests assigned</h3></div>'
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Student Dashboard</title>
    <style>
        body {{ font-family: Arial; margin: 0; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; }}
        .header {{ background: rgba(255,255,255,0.95); padding: 20px 0; }}
        .container {{ max-width: 1000px; margin: 20px auto; padding: 0 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat {{ background: rgba(255,255,255,0.95); padding: 20px; border-radius: 16px; text-align: center; }}
        .section {{ background: rgba(255,255,255,0.95); border-radius: 16px; padding: 24px; }}
        .logout {{ background: rgba(239,68,68,0.1); color: #dc2626; padding: 8px 16px; text-decoration: none; border-radius: 6px; float: right; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
            <h1 style="background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Engineer Dashboard
                <a href="/logout" class="logout">Logout</a>
            </h1>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat"><div style="font-size: 20px; font-weight: bold;">{len(my_tests)}</div><div>Tests</div></div>
            <div class="stat"><div style="font-size: 20px; font-weight: bold;">{len([t for t in my_tests if t['status'] == 'completed'])}</div><div>Done</div></div>
            <div class="stat"><div style="font-size: 20px; font-weight: bold;">{user.get('exp', 0)}y</div><div>Experience</div></div>
            <div class="stat"><div style="font-size: 20px; font-weight: bold;">1</div><div>Question</div></div>
        </div>
        
        <div class="section">
            <h2>My Tests</h2>
            {tests_html}
        </div>
    </div>
</body>
</html>'''

@app.route('/student/test/<test_id>', methods=['GET', 'POST'])
def student_test(test_id):
    if not session.get('user_id') or session.get('is_admin'):
        return redirect('/login')
    
    test = assignments.get(test_id)
    if not test or test['engineer_id'] != session['user_id']:
        return redirect('/student')
    
    if request.method == 'POST' and test['status'] == 'pending':
        answers = {}
        answer = request.form.get('answer_0', '').strip()
        if answer:
            answers['0'] = answer
        
        if len(answers) == 1:
            test['answers'] = answers
            test['status'] = 'submitted'
        
        return redirect('/student')
    
    questions_html = ''
    for i, q in enumerate(test['questions']):
        questions_html += f'''
        <div style="background: rgba(255,255,255,0.95); border-radius: 16px; padding: 24px; margin: 20px 0;">
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-bottom: 16px;">
                Question {i+1} of 1
            </div>
            <div style="background: linear-gradient(135deg, #f8fafc, #f1f5f9); padding: 16px; border-radius: 12px; margin-bottom: 20px; border-left: 4px solid #667eea;">
                {q}
            </div>
            <label style="font-weight: 600; margin-bottom: 8px; display: block;">Your Answer:</label>
            <textarea name="answer_{i}" style="width: 100%; min-height: 120px; padding: 16px; border: 2px solid #e5e7eb; border-radius: 12px; font-size: 14px;" placeholder="Provide detailed technical answer..." required></textarea>
        </div>'''
    
    topic_display = test["topic"].replace("_", " ").title()
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>{topic_display} Test</title>
    <style>
        body {{ font-family: Arial; margin: 0; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; }}
        .header {{ background: rgba(255,255,255,0.95); padding: 20px 0; position: sticky; top: 0; }}
        .container {{ max-width: 1000px; margin: 20px auto; padding: 0 20px; }}
        button {{ padding: 14px 28px; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; margin: 8px; }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; }}
        .btn-secondary {{ background: rgba(107,114,128,0.1); color: #374151; }}
        textarea:focus {{ outline: none; border-color: #667eea; }}
    </style>
</head>
<body>
    <div class="header">
        <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px; text-align: center;">
            <h1 style="background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {topic_display} Test
            </h1>
        </div>
    </div>
    
    <div class="container">
        <form method="POST">
            {questions_html}
            <div style="background: rgba(255,255,255,0.95); border-radius: 16px; padding: 24px; text-align: center; margin-top: 20px;">
                <div style="background: #fef3c7; border: 1px solid #f59e0b; padding: 16px; border-radius: 12px; margin-bottom: 20px; color: #92400e;">
                    ⚠️ Review all answers before submitting. Cannot edit after submission.
                </div>
                <button type="submit" class="btn-primary">Submit Test</button>
                <a href="/student"><button type="button" class="btn-secondary">Back</button></a>
            </div>
        </form>
    </div>
</body>
</html>'''

# Initialize
init_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

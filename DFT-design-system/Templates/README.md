# 🚀 Physical Design Assignment System

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy)

## 🎯 One-Click Deployment

Complete role-based assignment management system for physical design engineering with advanced technical evaluation.

## ✨ Features

### 🛡️ Admin Role
- ✅ View all engineer submissions with technical analysis
- ✅ Assign final grades and feedback  
- ✅ Control grade release timing
- ✅ System analytics and monitoring

### 👨‍💻 Engineer Role  
- ✅ Submit technical assignments (15 questions each)
- ✅ Real-time writing feedback and validation
- ✅ View released grades and admin feedback
- ❌ Cannot see other engineers' work (secure isolation)

### 🔍 Advanced Technical Evaluation
- **📊 Multi-dimensional scoring**: Technical terms (40%), Concepts (30%), Methodology (20%), Practical (10%)
- **🎯 Domain expertise**: Specialized for floorplanning, placement, and routing
- **📈 Detailed feedback**: Specific suggestions for improvement

## 🔐 Demo Accounts

| Role | Username | Password | Access |
|------|----------|----------|---------|
| **Admin** | `admin` | `admin123` | Full system access |
| **Engineer** | `engineer1` | `eng123` | Submit assignments |
| **Engineer** | `engineer2` | `eng123` | View released grades |

## 🚀 Quick Deploy to Railway

1. **Click the "Deploy on Railway" button above**
2. **Connect your GitHub account** 
3. **Railway will automatically deploy**
4. **Access your app** at the provided URL

## 🔧 Local Development

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/physical-design-system
cd physical-design-system

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Visit: `http://localhost:5000`

## 📱 System Health

- **Health check**: `/health`
- **Database**: Auto-initialized with demo data
- **Security**: Role-based access, CSRF protection, rate limiting

## 🎓 Topics Covered

- **Floorplanning**: Macro placement, power planning, thermal management
- **Placement**: Timing optimization, congestion management, clock considerations  
- **Routing**: DRC resolution, layer assignment, signal integrity

## 🏗️ Architecture

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite (auto-created)
- **Frontend**: Responsive HTML/CSS/JavaScript
- **Security**: Flask-Login, CSRF protection, input validation
- **Deployment**: Railway with health monitoring

## 📊 Workflow

1. **Admin creates assignments** → Engineers receive assignments
2. **Engineers submit answers** → System performs technical evaluation
3. **Admin reviews & grades** → Controls grade release timing
4. **Engineers view results** → Only released grades visible

## 🔐 Security Features

- ✅ Password hashing with Werkzeug
- ✅ CSRF protection on all forms
- ✅ Rate limiting on submissions (3 per hour)
- ✅ Role-based access control
- ✅ Input validation and sanitization

## 📈 Technical Evaluation

The system automatically evaluates submissions on:

1. **Technical Terms (40%)**: Domain-specific vocabulary analysis
2. **Concept Coverage (30%)**: Key engineering concepts evaluation  
3. **Methodology (20%)**: Problem-solving approach assessment
4. **Practical Application (10%)**: Real-world examples and specifics

## 🎯 Getting Started

1. **Deploy using Railway button above**
2. **Login as admin**: `admin` / `admin123`
3. **Create demo assignments**: Click "Create Demo Assignments"
4. **Login as engineer**: `engineer1` / `eng123`
5. **Submit assignment**: Complete technical questions
6. **Grade as admin**: Review and assign grades
7. **View results**: Engineer sees released grades

## 📞 Support

For deployment issues:
1. Check `/health` endpoint status
2. Review Railway deployment logs
3. Verify demo account credentials
4. Test role-based access

## 📝 License

Open source - modify and adapt for your educational needs.

---

**🚀 Ready to deploy? Click the Railway button at the top!**

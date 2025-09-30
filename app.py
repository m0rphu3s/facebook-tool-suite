from flask import Flask, request, render_template_string, redirect, url_for, session, flash, jsonify
import requests
import json
import os
import time
import threading
import uuid
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  access_key TEXT UNIQUE NOT NULL,
                  approved INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tokens
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  token TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

init_db()

# Global variables for task management
running_tasks = {}
stop_events = {}

# Welcome page with animation
WELCOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Lucifer Tool Suite</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(45deg, #000000, #1a1a1a, #333333, #000000);
            background-size: 400% 400%;
            animation: gradientShift 8s ease infinite;
            color: white;
            font-family: 'Arial', sans-serif;
            height: 100vh;
            overflow: hidden;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .welcome-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
            position: relative;
        }
        
        .logo-container {
            margin-bottom: 30px;
            animation: logoFloat 3s ease-in-out infinite;
        }
        
        .logo-container img {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 3px solid #ff0000;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.5);
        }
        
        @keyframes logoFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        .welcome-text {
            font-size: 4rem;
            font-weight: bold;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #ff0000, #ff6600, #ffaa00, #ff0000);
            background-size: 400% 400%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: textGlow 3s ease-in-out infinite, gradientShift 4s ease infinite;
            text-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
        }
        
        @keyframes textGlow {
            0%, 100% { text-shadow: 0 0 20px rgba(255, 0, 0, 0.5); }
            50% { text-shadow: 0 0 40px rgba(255, 0, 0, 0.8), 0 0 60px rgba(255, 0, 0, 0.6); }
        }
        
        .subtitle {
            font-size: 1.5rem;
            margin-bottom: 40px;
            opacity: 0;
            animation: fadeInUp 2s ease 1s forwards;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .enter-btn {
            padding: 15px 40px;
            font-size: 1.2rem;
            background: linear-gradient(45deg, #ff0000, #ff6600);
            border: none;
            border-radius: 50px;
            color: white;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            opacity: 0;
            animation: fadeInUp 2s ease 1.5s forwards;
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.3);
        }
        
        .enter-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(255, 0, 0, 0.5);
            background: linear-gradient(45deg, #ff6600, #ff0000);
        }
        
        .particles {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: #ff0000;
            border-radius: 50%;
            animation: float 6s infinite linear;
        }
        
        @keyframes float {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(-100px) rotate(360deg);
                opacity: 0;
            }
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    <div class="welcome-container">
        <div class="logo-container">
            <img src="/static/images/2353d19c3a21b405cdc0c35986199153.jpg" alt="Lucifer Logo">
        </div>
        <h1 class="welcome-text">WELCOME TO LUCIFER TOOL SUITE</h1>
        <p class="subtitle">Ultimate Facebook Automation & Management Platform</p>
        <a href="/login" class="enter-btn">ENTER THE REALM</a>
    </div>

    <script>
        // Create floating particles
        function createParticle() {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 6 + 's';
            particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
            document.getElementById('particles').appendChild(particle);
            
            setTimeout(() => {
                particle.remove();
            }, 6000);
        }
        
        setInterval(createParticle, 300);
        
        // Auto redirect after 10 seconds
        setTimeout(() => {
            window.location.href = '/login';
        }, 10000);
    </script>
</body>
</html>
"""

# Login/Register page
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Lucifer Tool Suite</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(45deg, #000000, #1a1a1a);
            color: white;
            min-height: 100vh;
            font-family: 'Arial', sans-serif;
        }
        
        .container {
            max-width: 400px;
            margin-top: 50px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.3);
            border: 1px solid rgba(255, 0, 0, 0.2);
        }
        
        .form-control {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            color: white;
            border-radius: 10px;
        }
        
        .form-control:focus {
            background: rgba(255, 255, 255, 0.15);
            border-color: #ff0000;
            color: white;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #ff0000, #ff6600);
            border: none;
            border-radius: 10px;
            padding: 12px;
            font-weight: bold;
        }
        
        .btn-primary:hover {
            background: linear-gradient(45deg, #ff6600, #ff0000);
            transform: translateY(-2px);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo img {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: 2px solid #ff0000;
        }
        
        .tab-buttons {
            display: flex;
            margin-bottom: 20px;
        }
        
        .tab-btn {
            flex: 1;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            color: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            background: linear-gradient(45deg, #ff0000, #ff6600);
        }
        
        .tab-btn:first-child {
            border-radius: 10px 0 0 10px;
        }
        
        .tab-btn:last-child {
            border-radius: 0 10px 10px 0;
        }
        
        .form-section {
            display: none;
        }
        
        .form-section.active {
            display: block;
        }
        
        .alert {
            border-radius: 10px;
            border: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="/static/images/2353d19c3a21b405cdc0c35986199153.jpg" alt="Logo">
            <h3 class="mt-3">LUCIFER TOOL SUITE</h3>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-warning">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="tab-buttons">
            <div class="tab-btn active" onclick="showTab('login')">LOGIN</div>
            <div class="tab-btn" onclick="showTab('register')">REGISTER</div>
        </div>
        
        <!-- Login Form -->
        <div id="login" class="form-section active">
            <form method="POST" action="/login">
                <input type="hidden" name="action" value="login">
                <div class="mb-3">
                    <label class="form-label">Access Key</label>
                    <input type="text" class="form-control" name="access_key" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">LOGIN</button>
            </form>
        </div>
        
        <!-- Register Form -->
        <div id="register" class="form-section">
            <form method="POST" action="/login">
                <input type="hidden" name="action" value="register">
                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <input type="text" class="form-control" name="username" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-control" name="email" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">REGISTER</button>
            </form>
            <p class="text-center mt-3 small">After registration, wait for admin approval to access tools.</p>
        </div>
    </div>
    
    <script>
        function showTab(tab) {
            document.querySelectorAll('.form-section').forEach(section => {
                section.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

# Dashboard HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Lucifer Tool Suite</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            background: linear-gradient(45deg, #000000, #1a1a1a);
            color: white;
            min-height: 100vh;
            font-family: 'Arial', sans-serif;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 0, 0, 0.3);
        }
        
        .navbar-brand {
            color: white !important;
            font-weight: bold;
        }
        
        .nav-link {
            color: white !important;
        }
        
        .tool-card {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(255, 0, 0, 0.3);
            border-color: #ff0000;
        }
        
        .tool-icon {
            font-size: 3rem;
            color: #ff0000;
            margin-bottom: 15px;
        }
        
        .btn-tool {
            background: linear-gradient(45deg, #ff0000, #ff6600);
            border: none;
            border-radius: 10px;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
        }
        
        .btn-tool:hover {
            background: linear-gradient(45deg, #ff6600, #ff0000);
            color: white;
            transform: translateY(-2px);
        }
        
        .uptime-badge {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #00ff00, #00aa00);
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(0, 255, 0, 0.3);
        }
        
        .logo-gallery {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        
        .logo-item {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: 2px solid #ff0000;
            transition: all 0.3s ease;
        }
        
        .logo-item:hover {
            transform: scale(1.1);
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
        }
    </style>
</head>
<body>
    <div class="uptime-badge">
        <i class="fas fa-clock"></i> Uptime: <span id="uptime">0 days</span>
    </div>
    
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="#">
                <img src="/static/images/2353d19c3a21b405cdc0c35986199153.jpg" width="40" height="40" class="rounded-circle me-2">
                LUCIFER TOOL SUITE
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/logout">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="text-center mb-4">
            <h1>Welcome, {{ username }}!</h1>
            <p class="lead">Choose your tool from the arsenal below</p>
        </div>
        
        <!-- Logo Gallery -->
        <div class="logo-gallery">
            <img src="/static/images/2353d19c3a21b405cdc0c35986199153.jpg" class="logo-item" alt="Logo 1">
            <img src="/static/images/ee3eca8923ea4714dfd76a18ba29558c.jpg" class="logo-item" alt="Logo 2">
            <img src="/static/images/ca122d8b3718d31db39a9159e8d2f5d6.jpg" class="logo-item" alt="Logo 3">
            <img src="/static/images/6566072d698ec8c6fb84220a7b944450.jpg" class="logo-item" alt="Logo 4">
            <img src="/static/images/goku_bg.jpg" class="logo-item" alt="Logo 5">
        </div>
        
        <div class="row">
            <div class="col-md-6 col-lg-4">
                <div class="tool-card text-center" onclick="location.href='/token-checker'">
                    <div class="tool-icon">
                        <i class="fas fa-key"></i>
                    </div>
                    <h4>Token Checker</h4>
                    <p>Validate Facebook access tokens</p>
                    <a href="/token-checker" class="btn-tool">Launch Tool</a>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4">
                <div class="tool-card text-center" onclick="location.href='/post-viewer'">
                    <div class="tool-icon">
                        <i class="fas fa-eye"></i>
                    </div>
                    <h4>Post Viewer</h4>
                    <p>View all Facebook posts from any profile</p>
                    <a href="/post-viewer" class="btn-tool">Launch Tool</a>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4">
                <div class="tool-card text-center" onclick="location.href='/post-commenter'">
                    <div class="tool-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <h4>Post Commenter</h4>
                    <p>Automatically comment on posts</p>
                    <a href="/post-commenter" class="btn-tool">Launch Tool</a>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4">
                <div class="tool-card text-center" onclick="location.href='/group-uid-fetcher'">
                    <div class="tool-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <h4>Group UID Fetcher</h4>
                    <p>Get UIDs from Messenger groups</p>
                    <a href="/group-uid-fetcher" class="btn-tool">Launch Tool</a>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4">
                <div class="tool-card text-center" onclick="location.href='/multi-convo'">
                    <div class="tool-icon">
                        <i class="fas fa-broadcast-tower"></i>
                    </div>
                    <h4>Multi Convo</h4>
                    <p>Send messages to multiple conversations</p>
                    <a href="/multi-convo" class="btn-tool">Launch Tool</a>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4">
                <div class="tool-card text-center" onclick="location.href='/uptime-monitor'">
                    <div class="tool-icon">
                        <i class="fas fa-heartbeat"></i>
                    </div>
                    <h4>Uptime Monitor</h4>
                    <p>Monitor system uptime and performance</p>
                    <a href="/uptime-monitor" class="btn-tool">Launch Tool</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Update uptime counter
        let startTime = Date.now();
        
        function updateUptime() {
            const now = Date.now();
            const uptime = now - startTime;
            const days = Math.floor(uptime / (1000 * 60 * 60 * 24));
            const hours = Math.floor((uptime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
            
            document.getElementById('uptime').textContent = `${days}d ${hours}h ${minutes}m`;
        }
        
        setInterval(updateUptime, 60000); // Update every minute
        updateUptime(); // Initial update
    </script>
</body>
</html>
"""

@app.route('/')
def welcome():
    return render_template_string(WELCOME_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            access_key = request.form.get('access_key')
            
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE access_key = ? AND approved = 1', (access_key,))
            user = c.fetchone()
            conn.close()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid access key or account not approved yet!')
        
        elif action == 'register':
            username = request.form.get('username')
            email = request.form.get('email')
            access_key = str(uuid.uuid4())
            
            try:
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute('INSERT INTO users (username, email, access_key) VALUES (?, ?, ?)',
                         (username, email, access_key))
                conn.commit()
                conn.close()
                
                flash(f'Registration successful! Your access key is: {access_key}. Please wait for admin approval.')
            except sqlite3.IntegrityError:
                flash('Username or email already exists!')
    
    return render_template_string(LOGIN_HTML)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template_string(DASHBOARD_HTML, username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

# Token Checker Tool
@app.route('/token-checker', methods=['GET', 'POST'])
def token_checker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    result = None
    if request.method == 'POST':
        token = request.form.get('token')
        try:
            url = f"https://graph.facebook.com/me?access_token={token}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                result = {
                    'status': 'Valid',
                    'name': data.get('name', 'N/A'),
                    'id': data.get('id', 'N/A')
                }
            else:
                result = {'status': 'Invalid', 'error': response.json().get('error', {}).get('message', 'Unknown error')}
        except Exception as e:
            result = {'status': 'Error', 'error': str(e)}
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Token Checker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(45deg, #000000, #1a1a1a); color: white; min-height: 100vh; }
            .container { max-width: 600px; margin-top: 50px; background: rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; }
            .form-control { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,0,0,0.3); color: white; }
            .btn-primary { background: linear-gradient(45deg, #ff0000, #ff6600); border: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-center mb-4">🔑 Token Checker</h2>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Facebook Access Token</label>
                    <input type="text" class="form-control" name="token" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Check Token</button>
            </form>
            
            {% if result %}
            <div class="mt-4 p-3 border rounded">
                <h5>Result:</h5>
                <p><strong>Status:</strong> {{ result.status }}</p>
                {% if result.status == 'Valid' %}
                    <p><strong>Name:</strong> {{ result.name }}</p>
                    <p><strong>ID:</strong> {{ result.id }}</p>
                {% else %}
                    <p><strong>Error:</strong> {{ result.error }}</p>
                {% endif %}
            </div>
            {% endif %}
            
            <div class="text-center mt-3">
                <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html, result=result)

# Post Viewer Tool
@app.route('/post-viewer', methods=['GET', 'POST'])
def post_viewer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    posts = []
    if request.method == 'POST':
        token = request.form.get('token')
        user_id = request.form.get('user_id', 'me')
        
        try:
            url = f"https://graph.facebook.com/v15.0/{user_id}/posts?fields=id,message,created_time,likes.summary(true),comments.summary(true)&access_token={token}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', [])
            else:
                posts = [{'error': response.json().get('error', {}).get('message', 'Unknown error')}]
        except Exception as e:
            posts = [{'error': str(e)}]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Post Viewer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(45deg, #000000, #1a1a1a); color: white; min-height: 100vh; }
            .container { max-width: 800px; margin-top: 50px; }
            .form-container { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; margin-bottom: 30px; }
            .post-card { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,0,0,0.3); border-radius: 10px; padding: 20px; margin-bottom: 20px; }
            .form-control { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,0,0,0.3); color: white; }
            .btn-primary { background: linear-gradient(45deg, #ff0000, #ff6600); border: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="form-container">
                <h2 class="text-center mb-4">👁️ Post Viewer</h2>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Facebook Access Token</label>
                        <input type="text" class="form-control" name="token" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">User ID (leave empty for your posts)</label>
                        <input type="text" class="form-control" name="user_id" placeholder="me">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Load Posts</button>
                </form>
            </div>
            
            {% if posts %}
            <div class="posts-container">
                <h3>Posts:</h3>
                {% for post in posts %}
                <div class="post-card">
                    {% if post.get('error') %}
                        <p class="text-danger">Error: {{ post.error }}</p>
                    {% else %}
                        <p><strong>Post ID:</strong> {{ post.id }}</p>
                        <p><strong>Message:</strong> {{ post.message or 'No message' }}</p>
                        <p><strong>Created:</strong> {{ post.created_time }}</p>
                        <p><strong>Likes:</strong> {{ post.likes.summary.total_count if post.likes else 0 }}</p>
                        <p><strong>Comments:</strong> {{ post.comments.summary.total_count if post.comments else 0 }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="text-center mt-3">
                <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html, posts=posts)

# Group UID Fetcher (using existing script)
@app.route('/group-uid-fetcher', methods=['GET', 'POST'])
def group_uid_fetcher():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    groups = []
    if request.method == "POST":
        token = request.form.get("token")
        try:
            url = f"https://graph.facebook.com/v15.0/me/conversations?fields=id,name&access_token={token}"
            res = requests.get(url).json()
            if "data" in res:
                groups = res["data"]
            else:
                groups = [{"name": "❌ Error", "id": res.get("error", {}).get("message", "Invalid Token")}]
        except Exception as e:
            groups = [{"name": "❌ Exception", "id": str(e)}]
    
    HTML_PAGE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Messenger Group UID Fetcher</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(45deg, #000000, #1a1a1a); color: white; min-height: 100vh; }
            .container { max-width: 800px; margin-top: 50px; background: rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; }
            .form-control { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,0,0,0.3); color: white; }
            .btn-primary { background: linear-gradient(45deg, #ff0000, #ff6600); border: none; }
            .table-dark { background: rgba(255,255,255,0.1); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mb-4">📌 Messenger Group UID Fetcher</h1>
            <form method="POST" class="mb-4">
                <div class="mb-3">
                    <label for="token" class="form-label">Enter Access Token:</label>
                    <input type="text" class="form-control" id="token" name="token" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Fetch Groups</button>
            </form>
            {% if groups %}
            <h3>✅ Groups Found:</h3>
            <table class="table table-dark table-bordered mt-3">
                <thead>
                    <tr>
                        <th>Group Name</th>
                        <th>Group UID</th>
                    </tr>
                </thead>
                <tbody>
                    {% for g in groups %}
                    <tr>
                        <td>{{ g.name }}</td>
                        <td>{{ g.id }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            <div class="text-center mt-3">
                <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(HTML_PAGE, groups=groups)

# Post Commenter Tool
@app.route('/post-commenter', methods=['GET', 'POST'])
def post_commenter():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        token = request.form.get('token')
        post_id = request.form.get('post_id')
        comment = request.form.get('comment')
        
        try:
            url = f"https://graph.facebook.com/v15.0/{post_id}/comments"
            data = {
                'message': comment,
                'access_token': token
            }
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                flash('Comment posted successfully!')
            else:
                flash(f'Error: {response.json().get("error", {}).get("message", "Unknown error")}')
        except Exception as e:
            flash(f'Exception: {str(e)}')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Post Commenter</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(45deg, #000000, #1a1a1a); color: white; min-height: 100vh; }
            .container { max-width: 600px; margin-top: 50px; background: rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; }
            .form-control { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,0,0,0.3); color: white; }
            .btn-primary { background: linear-gradient(45deg, #ff0000, #ff6600); border: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-center mb-4">💬 Post Commenter</h2>
            
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert alert-info">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Facebook Access Token</label>
                    <input type="text" class="form-control" name="token" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Post ID</label>
                    <input type="text" class="form-control" name="post_id" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Comment</label>
                    <textarea class="form-control" name="comment" rows="3" required></textarea>
                </div>
                <button type="submit" class="btn btn-primary w-100">Post Comment</button>
            </form>
            
            <div class="text-center mt-3">
                <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html)

# Multi Convo Tool
@app.route('/multi-convo', methods=['GET', 'POST'])
def multi_convo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        
        txt_file = request.files['txtFile']
        access_tokens = txt_file.read().decode().splitlines()
        
        messages_file = request.files['messagesFile']
        messages = messages_file.read().decode().splitlines()
        
        # Start the messaging task in a separate thread
        task_id = str(uuid.uuid4())
        stop_event = threading.Event()
        stop_events[task_id] = stop_event
        
        def send_messages():
            post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
            headers = {'Content-Type': 'application/json'}
            
            num_comments = len(messages)
            max_tokens = len(access_tokens)
            
            while not stop_event.is_set():
                try:
                    for message_index in range(num_comments):
                        if stop_event.is_set():
                            break
                            
                        token_index = message_index % max_tokens
                        access_token = access_tokens[token_index]
                        message = messages[message_index].strip()
                        
                        parameters = {
                            'access_token': access_token,
                            'message': mn + ' ' + message
                        }
                        
                        response = requests.post(post_url, json=parameters, headers=headers)
                        current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                        
                        if response.ok:
                            print(f"[+] SEND SUCCESSFUL No. {message_index + 1} Post Id {post_url} Token No.{token_index + 1}: {mn + ' ' + message}")
                            print(f"  - Time: {current_time}")
                        else:
                            print(f"[x] Failed to send Comment No. {message_index + 1} Post Id {post_url} Token No. {token_index + 1}: {mn + ' ' + message}")
                            print(f"  - Time: {current_time}")
                        
                        time.sleep(time_interval)
                        
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=send_messages)
        thread.daemon = True
        thread.start()
        
        running_tasks[task_id] = thread
        flash(f'Multi Convo started! Task ID: {task_id}')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi Convo</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(45deg, #000000, #1a1a1a); color: white; min-height: 100vh; }
            .container { max-width: 600px; margin-top: 50px; background: rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; }
            .form-control { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,0,0,0.3); color: white; }
            .btn-primary { background: linear-gradient(45deg, #ff0000, #ff6600); border: none; }
            .btn-danger { background: linear-gradient(45deg, #ff0000, #aa0000); border: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-center mb-4">📡 Multi Convo</h2>
            
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert alert-info">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3">
                    <label class="form-label">Convo ID</label>
                    <input type="text" class="form-control" name="threadId" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Select Your Tokens File</label>
                    <input type="file" class="form-control" name="txtFile" accept=".txt" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Select Your Messages File</label>
                    <input type="file" class="form-control" name="messagesFile" accept=".txt" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Enter Hater Name</label>
                    <input type="text" class="form-control" name="kidx" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Speed in Seconds</label>
                    <input type="number" class="form-control" name="time" value="60" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Start Multi Convo</button>
            </form>
            
            <hr>
            
            <form method="POST" action="/stop-task">
                <div class="mb-3">
                    <label class="form-label">Enter Task ID to Stop</label>
                    <input type="text" class="form-control" name="taskId" required>
                </div>
                <button type="submit" class="btn btn-danger w-100">Stop Task</button>
            </form>
            
            <div class="text-center mt-3">
                <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html)

@app.route('/stop-task', methods=['POST'])
def stop_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        flash(f'Task with ID {task_id} has been stopped.')
    else:
        flash(f'No task found with ID {task_id}.')
    
    return redirect(url_for('multi_convo'))

# Uptime Monitor
@app.route('/uptime-monitor')
def uptime_monitor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get system uptime
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        uptime_str = f"{days} days, {hours} hours, {minutes} minutes"
    except:
        uptime_str = "Unable to determine uptime"
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Uptime Monitor</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(45deg, #000000, #1a1a1a); color: white; min-height: 100vh; }
            .container { max-width: 800px; margin-top: 50px; background: rgba(255,255,255,0.1); border-radius: 15px; padding: 30px; }
            .uptime-card { background: rgba(0,255,0,0.1); border: 1px solid rgba(0,255,0,0.3); border-radius: 10px; padding: 20px; margin-bottom: 20px; }
            .status-online { color: #00ff00; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="text-center mb-4">💓 Uptime Monitor</h2>
            
            <div class="uptime-card text-center">
                <h3 class="status-online">🟢 SYSTEM ONLINE</h3>
                <h4>Current Uptime: {{ uptime }}</h4>
                <p>Target: 100 days non-stop operation</p>
                <p>Status: Monitoring active</p>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="card bg-dark border-success">
                        <div class="card-body text-center">
                            <h5 class="text-success">CPU Status</h5>
                            <p class="status-online">✅ Normal</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-dark border-success">
                        <div class="card-body text-center">
                            <h5 class="text-success">Memory</h5>
                            <p class="status-online">✅ Available</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-dark border-success">
                        <div class="card-body text-center">
                            <h5 class="text-success">Network</h5>
                            <p class="status-online">✅ Connected</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="text-center mt-4">
                <button class="btn btn-success" onclick="location.reload()">Refresh Status</button>
                <a href="/dashboard" class="btn btn-secondary ms-2">Back to Dashboard</a>
            </div>
        </div>
        
        <script>
            // Auto refresh every 30 seconds
            setTimeout(() => {
                location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html, uptime=uptime_str)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

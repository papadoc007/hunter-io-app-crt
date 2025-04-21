from http.server import BaseHTTPRequestHandler
import os
import json
import re
import secrets
from datetime import datetime
from functools import wraps
import base64
import traceback

import requests
from flask import Flask, Response, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

# יצירת אפליקציית Flask בסיסית
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['HUNTER_API_KEY'] = os.getenv('HUNTER_API_KEY', '57c44309d360d1a010022848682937418db899be')
app.config['ALLOWED_DOMAIN'] = 'crt-imp.com'  # הדומיין המורשה

# מודלים בסיסיים - במקום מסד נתונים נשתמש באובייקטים בזיכרון (לדוגמה והדגמה)
users = {
    "admin@crt-imp.com": {
        "password_hash": generate_password_hash("admin123"),
        "is_admin": True,
    },
    "user@crt-imp.com": {
        "password_hash": generate_password_hash("user123"),
        "is_admin": False,
    }
}

# שמירת חיפושים בזיכרון
search_history = {}

# פונקציית חיפוש רשמית
def perform_hunter_search(domain, company=""):
    api_key = app.config['HUNTER_API_KEY']
    if not api_key:
        return {"error": "לא נמצא מפתח API"}, 500
    
    # יצירת בקשה ל-Hunter.io API
    params = {
        'domain': domain,
        'api_key': api_key,
        'company': company if company else None
    }
    
    try:
        response = requests.get('https://api.hunter.io/v2/domain-search', params=params)
        results = response.json()
        return results
    except Exception as e:
        return {"error": str(e)}, 500

# מחלקת Handler לשרת Vercel Serverless
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # טיפול בבקשות GET בסיסיות
        if self.path == '/api/info':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            info = {
                "name": "Hunter.io API",
                "version": "1.0.0",
                "description": "API לחיפוש מידע באמצעות Hunter.io",
                "endpoints": [
                    {
                        "path": "/api/search",
                        "method": "POST",
                        "description": "חיפוש אימיילים לפי דומיין"
                    },
                    {
                        "path": "/api/login",
                        "method": "POST",
                        "description": "התחברות למערכת"
                    },
                    {
                        "path": "/api/history",
                        "method": "GET",
                        "description": "היסטוריית חיפושים של המשתמש"
                    }
                ],
                "status": "פעיל"
            }
            self.wfile.write(json.dumps(info, ensure_ascii=False).encode('utf-8'))
            return
        elif self.path.startswith('/api/history'):
            # בדיקת שהמשתמש מחובר - אם לא, מחזיר שגיאה
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Basic '):
                self.send_response(401)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "נדרשת התחברות"}, ensure_ascii=False).encode('utf-8'))
                return
                
            # פענוח פרטי ההתחברות
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            email, password = auth_decoded.split(':', 1)
            
            if email not in users or not check_password_hash(users[email]["password_hash"], password):
                self.send_response(401)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "פרטי התחברות שגויים"}, ensure_ascii=False).encode('utf-8'))
                return
                
            # אחזור היסטוריית חיפושים של המשתמש
            user_history = search_history.get(email, [])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"history": user_history}, ensure_ascii=False).encode('utf-8'))
            return
        
        # דף הבית
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
            
        html = """
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hunter.io חיפוש מידע</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    padding: 20px;
                    background-color: white;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    border-radius: 8px;
                    text-align: center;
                }
                h1 {
                    color: #3498db;
                }
                .search-form {
                    margin: 20px 0;
                    text-align: right;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 500;
                }
                .form-group input {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .links {
                    margin-top: 20px;
                }
                .links a, button {
                    display: inline-block;
                    margin: 10px;
                    padding: 10px 20px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                    border: none;
                    font-size: 1em;
                    cursor: pointer;
                }
                .links a:hover, button:hover {
                    background-color: #2980b9;
                }
                #results {
                    margin-top: 20px;
                    text-align: right;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }
                .hidden {
                    display: none;
                }
                #loginForm {
                    margin-top: 20px;
                    padding: 20px;
                    border-top: 1px solid #eee;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hunter.io חיפוש מידע</h1>
                <p>חיפוש כתובות אימייל לפי דומיין</p>
                
                <div id="loginSection">
                    <button id="showLoginBtn">התחברות</button>
                    <div id="loginForm" class="hidden">
                        <h2>התחברות</h2>
                        <div class="form-group">
                            <label for="email">אימייל</label>
                            <input type="email" id="email" placeholder="user@crt-imp.com">
                        </div>
                        <div class="form-group">
                            <label for="password">סיסמה</label>
                            <input type="password" id="password">
                        </div>
                        <button id="loginBtn">התחבר</button>
                    </div>
                </div>
                
                <div id="searchSection" class="hidden">
                    <div class="search-form">
                        <div class="form-group">
                            <label for="domain">דומיין *</label>
                            <input type="text" id="domain" placeholder="לדוגמה: crt-imp.com" required>
                        </div>
                        <div class="form-group">
                            <label for="company">שם חברה (אופציונלי)</label>
                            <input type="text" id="company" placeholder="לדוגמה: Google">
                        </div>
                        <button id="searchBtn">חפש</button>
                    </div>
                    
                    <div id="results" class="hidden">
                        <h2>תוצאות חיפוש</h2>
                        <div id="resultsContent"></div>
                    </div>
                    
                    <button id="showHistoryBtn" class="hidden">היסטוריית חיפושים</button>
                    <div id="historyResults" class="hidden">
                        <h2>היסטוריית חיפושים</h2>
                        <div id="historyContent"></div>
                    </div>
                </div>
                
                <div class="links">
                    <a href="/api/info">מידע על API</a>
                    <a href="https://github.com/papadoc007/hunter-io-app-crt" target="_blank">קוד מקור ב-GitHub</a>
                </div>
            </div>
            
            <script>
                // מחזיק את המצב הנוכחי
                let currentUser = null;
                let authHeader = null;
                
                // כשהדף נטען
                document.addEventListener('DOMContentLoaded', function() {
                    // כפתורים
                    const showLoginBtn = document.getElementById('showLoginBtn');
                    const loginBtn = document.getElementById('loginBtn');
                    const searchBtn = document.getElementById('searchBtn');
                    const showHistoryBtn = document.getElementById('showHistoryBtn');
                    
                    // טפסים ואזורים
                    const loginForm = document.getElementById('loginForm');
                    const searchSection = document.getElementById('searchSection');
                    const results = document.getElementById('results');
                    const historyResults = document.getElementById('historyResults');
                    
                    // הצגת טופס התחברות
                    showLoginBtn.addEventListener('click', function() {
                        loginForm.classList.toggle('hidden');
                    });
                    
                    // התחברות
                    loginBtn.addEventListener('click', function() {
                        const email = document.getElementById('email').value;
                        const password = document.getElementById('password').value;
                        
                        // יצירת Basic Auth
                        authHeader = 'Basic ' + btoa(email + ':' + password);
                        
                        // שליחת בקשת התחברות
                        fetch('/api/login', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': authHeader
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert(data.error);
                                return;
                            }
                            
                            // שמירת המשתמש הנוכחי
                            currentUser = data.user;
                            
                            // הסתרת אזור ההתחברות והצגת אזור החיפוש
                            document.getElementById('loginSection').classList.add('hidden');
                            searchSection.classList.remove('hidden');
                            showHistoryBtn.classList.remove('hidden');
                            
                            // הצגת ברכה
                            alert('ברוך הבא, ' + currentUser.email);
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('שגיאה בהתחברות');
                        });
                    });
                    
                    // חיפוש
                    searchBtn.addEventListener('click', function() {
                        const domain = document.getElementById('domain').value;
                        const company = document.getElementById('company').value;
                        
                        if (!domain) {
                            alert('אנא הזן דומיין לחיפוש');
                            return;
                        }
                        
                        // הצגת הודעת טעינה
                        results.classList.remove('hidden');
                        document.getElementById('resultsContent').innerHTML = '<p>מחפש נתונים...</p>';
                        
                        // שליחת בקשת חיפוש
                        fetch('/api/search', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': authHeader
                            },
                            body: JSON.stringify({ domain, company })
                        })
                        .then(response => response.json())
                        .then(data => {
                            // הצגת התוצאות
                            displayResults(data);
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            document.getElementById('resultsContent').innerHTML = '<p>אירעה שגיאה בחיפוש</p>';
                        });
                    });
                    
                    // הצגת היסטוריה
                    showHistoryBtn.addEventListener('click', function() {
                        // הצגת הודעת טעינה
                        historyResults.classList.remove('hidden');
                        document.getElementById('historyContent').innerHTML = '<p>טוען היסטוריה...</p>';
                        
                        // שליחת בקשה להיסטוריה
                        fetch('/api/history', {
                            method: 'GET',
                            headers: {
                                'Authorization': authHeader
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            // הצגת ההיסטוריה
                            displayHistory(data);
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            document.getElementById('historyContent').innerHTML = '<p>אירעה שגיאה בטעינת ההיסטוריה</p>';
                        });
                    });
                    
                    // הצגת תוצאות החיפוש
                    function displayResults(data) {
                        let html = '';
                        
                        if (data.error) {
                            html = '<p>שגיאה: ' + data.error + '</p>';
                        } else if (data.data) {
                            const { domain, organization, emails, meta } = data.data;
                            
                            html = '<div>';
                            html += '<p><strong>דומיין:</strong> ' + (domain || '-') + '</p>';
                            html += '<p><strong>חברה:</strong> ' + (organization || '-') + '</p>';
                            html += '<p><strong>מספר תוצאות:</strong> ' + (meta ? meta.results : '0') + '</p>';
                            
                            if (emails && emails.length > 0) {
                                html += '<h3>כתובות אימייל:</h3><ul>';
                                
                                emails.forEach(email => {
                                    html += '<li>';
                                    html += '<strong>' + (email.value || '-') + '</strong><br>';
                                    
                                    if (email.first_name || email.last_name) {
                                        const name = (email.first_name || '') + ' ' + (email.last_name || '');
                                        html += name.trim();
                                    }
                                    
                                    if (email.position) {
                                        html += ', ' + email.position;
                                    }
                                    
                                    html += '<br>אמינות: ' + (email.confidence || '0') + '%';
                                    html += '</li>';
                                });
                                
                                html += '</ul>';
                            } else {
                                html += '<p>לא נמצאו כתובות אימייל</p>';
                            }
                            
                            html += '</div>';
                        } else {
                            html = '<p>לא התקבלו תוצאות</p>';
                        }
                        
                        document.getElementById('resultsContent').innerHTML = html;
                    }
                    
                    // הצגת היסטוריית החיפושים
                    function displayHistory(data) {
                        let html = '';
                        
                        if (data.error) {
                            html = '<p>שגיאה: ' + data.error + '</p>';
                        } else if (data.history && data.history.length > 0) {
                            html = '<ul>';
                            
                            data.history.forEach(item => {
                                html += '<li>';
                                html += '<strong>דומיין:</strong> ' + item.domain;
                                
                                if (item.company) {
                                    html += ', <strong>חברה:</strong> ' + item.company;
                                }
                                
                                html += '<br><strong>זמן:</strong> ' + item.timestamp;
                                html += '</li>';
                            });
                            
                            html += '</ul>';
                        } else {
                            html = '<p>אין היסטוריית חיפושים</p>';
                        }
                        
                        document.getElementById('historyContent').innerHTML = html;
                    }
                });
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
        return
        
    def do_POST(self):
        # טיפול בבקשות POST
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(post_data)
            
            # התחברות
            if self.path == '/api/login':
                # בדיקת שהמשתמש מחובר - אם לא, מחזיר שגיאה
                auth_header = self.headers.get('Authorization', '')
                if not auth_header.startswith('Basic '):
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "נדרשת התחברות"}, ensure_ascii=False).encode('utf-8'))
                    return
                    
                # פענוח פרטי ההתחברות
                auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
                email, password = auth_decoded.split(':', 1)
                
                if email not in users or not check_password_hash(users[email]["password_hash"], password):
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "פרטי התחברות שגויים"}, ensure_ascii=False).encode('utf-8'))
                    return
                    
                # התחברות מוצלחת
                user_info = {
                    "email": email,
                    "is_admin": users[email]["is_admin"]
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"user": user_info}, ensure_ascii=False).encode('utf-8'))
                return
                
            # חיפוש
            elif self.path == '/api/search':
                # בדיקת שהמשתמש מחובר - אם לא, מחזיר שגיאה
                auth_header = self.headers.get('Authorization', '')
                if not auth_header.startswith('Basic '):
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "נדרשת התחברות"}, ensure_ascii=False).encode('utf-8'))
                    return
                    
                # פענוח פרטי ההתחברות
                auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
                email, password = auth_decoded.split(':', 1)
                
                if email not in users or not check_password_hash(users[email]["password_hash"], password):
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "פרטי התחברות שגויים"}, ensure_ascii=False).encode('utf-8'))
                    return
                
                # חיפוש
                domain = data.get('domain', '')
                company = data.get('company', '')
                
                if not domain:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "נדרש דומיין לחיפוש"}, ensure_ascii=False).encode('utf-8'))
                    return
                
                # ביצוע החיפוש
                results = perform_hunter_search(domain, company)
                
                # שמירת החיפוש בהיסטוריה
                if email not in search_history:
                    search_history[email] = []
                    
                search_history[email].append({
                    "domain": domain,
                    "company": company,
                    "timestamp": datetime.now().isoformat()
                })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf-8'))
                return
            else:
                # נתיב לא ידוע
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "נתיב לא קיים"}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            # שגיאה בעיבוד הבקשה
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_details = {
                "error": f"שגיאה בעיבוד הבקשה: {str(e)}",
                "traceback": traceback.format_exc()
            }
            self.wfile.write(json.dumps(error_details, ensure_ascii=False).encode('utf-8')) 
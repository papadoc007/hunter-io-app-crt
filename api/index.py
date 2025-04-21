from http.server import BaseHTTPRequestHandler
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import requests

# יצירת אפליקציית Flask בסיסית
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

# נתיב ראשי לבדיקה
@app.route('/')
def home():
    return "האפליקציה של Hunter.io עובדת! זו גרסת הבדיקה."

# API נתיב לחיפוש (דוגמה)
@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    domain = data.get('domain', '')
    company = data.get('company', '')
    
    # תשובת דוגמה
    result = {
        "status": "success",
        "domain": domain,
        "company": company,
        "timestamp": datetime.now().isoformat(),
        "message": "פונקציונליות החיפוש תהיה זמינה בקרוב"
    }
    
    return jsonify(result)

# מחלקת Handler לשרת Vercel Serverless
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # טיפול בבקשות GET בסיסיות
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        if self.path == '/api/info':
            info = {
                "name": "Hunter.io API",
                "version": "1.0.0",
                "description": "API לחיפוש מידע באמצעות Hunter.io",
                "endpoints": [
                    {
                        "path": "/api/search",
                        "method": "POST",
                        "description": "חיפוש אימיילים לפי דומיין"
                    }
                ],
                "status": "פעיל"
            }
            self.wfile.write(json.dumps(info, ensure_ascii=False).encode('utf-8'))
            return
            
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
                .links {
                    margin-top: 20px;
                }
                .links a {
                    display: inline-block;
                    margin: 10px;
                    padding: 10px 20px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                }
                .links a:hover {
                    background-color: #2980b9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hunter.io חיפוש מידע</h1>
                <p>האפליקציה מוכנה לשימוש! כעת ניתן להתחיל בפיתוח הממשק המלא.</p>
                <div class="links">
                    <a href="/api/info">מידע על API</a>
                    <a href="https://github.com/papadoc007/hunter-io-app-crt" target="_blank">קוד מקור ב-GitHub</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
        return
        
    def do_POST(self):
        # טיפול בבקשות POST
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
            
            if self.path == '/api/search':
                # תשובת דוגמה לחיפוש
                result = {
                    "status": "success",
                    "domain": data.get('domain', ''),
                    "company": data.get('company', ''),
                    "timestamp": datetime.now().isoformat(),
                    "message": "פונקציונליות החיפוש תהיה זמינה בקרוב"
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
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
            self.wfile.write(json.dumps({"error": f"שגיאה בעיבוד הבקשה: {str(e)}"}, ensure_ascii=False).encode('utf-8')) 
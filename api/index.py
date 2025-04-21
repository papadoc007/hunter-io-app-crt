from flask import Flask, request, jsonify, Response
import os
import json
import requests
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env אם קיים
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['HUNTER_API_KEY'] = os.environ.get('HUNTER_API_KEY', '')

# מסד נתונים מדומה למשתמשים לצרכי הדגמה
users = {
    'admin@example.com': {
        'password': generate_password_hash('admin123'),
        'is_admin': True
    },
    'user@example.com': {
        'password': generate_password_hash('user123'),
        'is_admin': False
    }
}

# מסד נתונים מדומה להיסטוריית חיפושים
search_history = {}

def perform_hunter_search(domain, api_key):
    """
    ביצוע חיפוש ב-Hunter.io API וסינון תוצאות אמיתיות בלבד
    """
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()
            
            # סינון תוצאות רק לתוצאות אמיתיות
            if 'data' in results and 'emails' in results['data']:
                # סינון רק אימיילים אמיתיים
                verified_emails = [email for email in results['data']['emails'] if email.get('verification', {}).get('status') == 'valid']
                results['data']['emails'] = verified_emails
                # עדכון מספר התוצאות
                if 'meta' in results['data']:
                    results['data']['meta']['results'] = len(verified_emails)
                    
            return results
        return {"error": f"Hunter API returned status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def token_required(f):
    """
    דקורטור לאימות JWT token
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['email']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    """
    נתיב להתחברות משתמש
    """
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Missing email or password'}), 400
        
    email = data['email']
    password = data['password']
    
    if email not in users:
        return jsonify({'message': 'User not found'}), 404
        
    if not check_password_hash(users[email]['password'], password):
        return jsonify({'message': 'Wrong password'}), 401
    
    # יצירת JWT token
    token = jwt.encode({
        'email': email,
        'is_admin': users[email]['is_admin'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'is_admin': users[email]['is_admin']
    }), 200

@app.route('/api/search', methods=['POST'])
@token_required
def search(current_user):
    """
    נתיב לביצוע חיפוש ב-Hunter.io
    """
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'message': 'Missing domain parameter'}), 400
    
    domain = data['domain']
    
    # שמירת החיפוש בהיסטוריה
    if current_user not in search_history:
        search_history[current_user] = []
    
    search_entry = {
        'domain': domain,
        'timestamp': datetime.utcnow().isoformat()
    }
    search_history[current_user].append(search_entry)
    
    # ביצוע חיפוש ב-Hunter.io
    result = perform_hunter_search(domain, app.config['HUNTER_API_KEY'])
    
    return jsonify(result), 200

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    """
    נתיב לקבלת היסטוריית חיפושים
    """
    if current_user not in search_history:
        return jsonify([]), 200
    
    return jsonify(search_history[current_user]), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    נתיב לבדיקת תקינות השירות
    """
    return jsonify({'status': 'ok'}), 200

# קוד להרצה מקומית
if __name__ == '__main__':
    app.run(debug=True) 

# Vercel serverless function handler
def handler(request, context):
    """
    פונקציית Handler לסביבת Vercel Serverless Functions
    """
    with app.request_context(request.environ):
        return app(request.environ, lambda status, headers: [status, headers]) 
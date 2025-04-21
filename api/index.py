from flask import Flask, request, jsonify
import os
import jwt
import datetime
import requests
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_for_dev')
app.config['HUNTER_API_KEY'] = os.environ.get('HUNTER_API_KEY', '')

# מוקאפ של מסד נתונים למשתמשים ולהיסטוריית חיפוש
mock_db = {
    'users': [
        {
            'id': 1,
            'email': 'admin@example.com',
            'password': 'sha256$pbkdf2:sha256:150000$DtdSQK7S$28dec47ac07dcd12c4a34b6a3b35561b0e118d5f2a8e788c55aae9e625da33c9',  # סיסמה: admin123
            'is_admin': True,
            'otp_secret': None,
            'otp_enabled': False
        }
    ],
    'search_history': []
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            bearer = request.headers['Authorization']
            if bearer.startswith('Bearer '):
                token = bearer[7:]

        if not token:
            return jsonify({'message': 'חסר טוקן אימות!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
            # במימוש אמיתי, נחפש את המשתמש במסד הנתונים
            # לצורך הדגמה, אנחנו בודקים במסד נתונים מוקאפ
            user = next((u for u in mock_db['users'] if u['id'] == user_id), None)
            if not user:
                return jsonify({'message': 'משתמש לא נמצא!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'פג תוקף הטוקן!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'טוקן לא חוקי!'}), 401

        return f(user, *args, **kwargs)
    return decorated

def perform_hunter_search(domain):
    api_key = app.config['HUNTER_API_KEY']
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return {"error": f"שגיאה בקריאה ל-API: {response.status_code}"}
    except Exception as e:
        return {"error": f"שגיאה בביצוע החיפוש: {str(e)}"}

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # במימוש אמיתי, נבדוק מול מסד הנתונים
    # לצורך הדגמה, בודק מול המוקאפ ומחזיר טוקן
    user = next((u for u in mock_db['users'] if u['email'] == email), None)
    if user and password == 'admin123':  # בפועל נשתמש בבדיקת האש
        token = jwt.encode(
            {
                'user_id': user['id'],
                'is_admin': user['is_admin'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        return jsonify({'token': token})
    
    return jsonify({'message': 'אימות נכשל!'}), 401

@app.route('/api/search', methods=['POST'])
@token_required
def search(current_user):
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'error': 'דומיין הוא שדה חובה'}), 400
    
    search_result = perform_hunter_search(domain)
    
    # שמירת החיפוש בהיסטוריה
    mock_db['search_history'].append({
        'user_id': current_user['id'],
        'domain': domain,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'result': search_result
    })
    
    return jsonify(search_result)

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    # במימוש אמיתי נמשוך מנתונים ממסד הנתונים
    user_history = [h for h in mock_db['search_history'] if h['user_id'] == current_user['id']]
    return jsonify(user_history)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'השירות פעיל'})

# נקודת כניסה עבור Vercel Serverless Function
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return app.response_class(
        response=jsonify({"message": "קצה API לא נמצא", "endpoint": path}),
        status=404
    )

# מאפשר ל-Vercel לקרוא לפונקציה
if __name__ == '__main__':
    app.run(debug=True)

# הגדרה עבור Vercel Serverless Functions
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Hello, World!'.encode())
        return 
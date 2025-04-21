import os
import json
from datetime import datetime
from io import BytesIO

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response, abort
import requests
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env (אופציונלי)
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'hunter_io_app_key')

# ניתוב ראשי - דף הבית
@app.route('/')
def index():
    return render_template('index.html')

# דף מידע על ה-API
@app.route('/api-info')
def api_info():
    return render_template('api_info.html')

# API חיפוש
@app.route('/search', methods=['POST'])
def search():
    data = request.json
    domain = data.get('domain')
    company = data.get('company', '')
    api_key = data.get('api_key', '')
    
    # בדיקת קלט
    if not domain:
        return jsonify({'error': 'נדרש דומיין לחיפוש'}), 400
    
    if not api_key:
        return jsonify({'error': 'נדרש מפתח API מ-Hunter.io'}), 400
    
    # יצירת בקשה ל-Hunter.io API
    params = {
        'domain': domain,
        'api_key': api_key,
        'company': company if company else None
    }
    
    try:
        response = requests.get('https://api.hunter.io/v2/domain-search', params=params)
        results = response.json()
        
        # בדיקה אם יש שגיאה בתשובה
        if 'errors' in results:
            return jsonify({'error': results['errors'][0]['details']}), 400
        
        # סינון תוצאות רק לתוצאות אמיתיות (ללא התחשבות בציון האמינות)
        if 'data' in results and 'emails' in results['data']:
            # שמירה רק על אימיילים אמיתיים
            verified_emails = [email for email in results['data']['emails'] if email.get('verification', {}).get('status') == 'valid']
            results['data']['emails'] = verified_emails
            # עדכון מספר התוצאות
            if 'meta' in results['data']:
                results['data']['meta']['results'] = len(verified_emails)
        
        # שמירת תוצאות החיפוש בהיסטוריה (בקוקיס)
        save_to_history(domain, company, results)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# שמירת חיפוש בהיסטוריה בקוקיס
def save_to_history(domain, company, results):
    search_history = session.get('search_history', [])
    
    # מגביל את ההיסטוריה ל-10 חיפושים אחרונים
    if len(search_history) >= 10:
        search_history.pop()
    
    # הוספת חיפוש חדש בתחילת הרשימה
    search_entry = {
        'domain': domain,
        'company': company,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'results': results
    }
    
    search_history.insert(0, search_entry)
    session['search_history'] = search_history

# היסטוריית חיפושים
@app.route('/history')
def get_history():
    search_history = session.get('search_history', [])
    return jsonify(search_history)

# ניקוי היסטוריה
@app.route('/clear-history', methods=['POST'])
def clear_history():
    session.pop('search_history', None)
    return jsonify({'success': True})

# שמירת מפתח API בקוקיס
@app.route('/save-api-key', methods=['POST'])
def save_api_key():
    data = request.json
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({'error': 'מפתח API ריק'}), 400
    
    session['api_key'] = api_key
    
    return jsonify({'success': True})

# קבלת מפתח API מהקוקיס
@app.route('/get-api-key')
def get_api_key():
    api_key = session.get('api_key', '')
    return jsonify({'api_key': api_key})

if __name__ == '__main__':
    app.run(debug=True) 
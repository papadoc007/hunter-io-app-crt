import os
import json
import re
import secrets
from datetime import datetime
from functools import wraps
from io import BytesIO

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, abort
import requests
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode
from PIL import Image
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

# טעינת משתני סביבה מקובץ .env
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///hunter_search.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['ALLOWED_DOMAIN'] = 'crt-imp.com'  # הדומיין המורשה
app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL', 'admin@crt-imp.com')  # משתמש מנהל

# ניהול משתמשים
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

# מודל למשתמשים
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    otp_secret = db.Column(db.String(32))
    otp_enabled = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_otp_uri(self):
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.email,
            issuer_name='Hunter.io Search'
        )
    
    def verify_otp(self, otp):
        return pyotp.TOTP(self.otp_secret).verify(otp)

# מודל לשמירת היסטוריית חיפושים
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    results = db.Column(db.Text, nullable=False)  # שמירת התוצאות כ-JSON
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('searches', lazy=True))

    def __repr__(self):
        return f'<SearchHistory {self.domain}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# טפסים
class LoginForm(FlaskForm):
    email = StringField('כתובת אימייל', validators=[DataRequired(), Email()])
    password = PasswordField('סיסמה', validators=[DataRequired()])
    otp = StringField('קוד אימות')
    remember_me = BooleanField('זכור אותי')
    submit = SubmitField('התחבר')

class RegistrationForm(FlaskForm):
    email = StringField('כתובת אימייל', validators=[DataRequired(), Email()])
    password = PasswordField('סיסמה', validators=[DataRequired()])
    password2 = PasswordField('אימות סיסמה', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('הירשם')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('כתובת האימייל כבר קיימת במערכת.')
        
        # בדיקת דומיין מאושר
        domain = email.data.split('@')[-1]
        if domain != app.config['ALLOWED_DOMAIN'] and email.data != app.config['ADMIN_EMAIL']:
            raise ValidationError(f'רק כתובות אימייל מהדומיין {app.config["ALLOWED_DOMAIN"]} מורשות להירשם.')

# פונקציית עזר - בדיקה אם המשתמש מנהל
def is_admin():
    return current_user.is_authenticated and current_user.is_admin

# דקורטור לבדיקת הרשאות מנהל
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# יצירת מסד הנתונים אם לא קיים
with app.app_context():
    db.create_all()
    
    # יצירת משתמש מנהל אם לא קיים
    admin_email = app.config['ADMIN_EMAIL']
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user and os.getenv('ADMIN_PASSWORD'):
        admin_user = User(email=admin_email, is_admin=True)
        admin_user.set_password(os.getenv('ADMIN_PASSWORD'))
        admin_user.otp_secret = pyotp.random_base32()
        db.session.add(admin_user)
        db.session.commit()
        print(f"משתמש מנהל נוצר: {admin_email}")

# ניתוב ראשי - מעבר לדף הבית אם המשתמש מחובר, אחרת מעבר לדף ההתחברות
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return redirect(url_for('login'))

# התחברות
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # אם 2FA מופעל, נדרש קוד אימות
            if user.otp_enabled:
                # אם נשלח קוד אימות, מוודא שהוא נכון
                if form.otp.data:
                    if user.verify_otp(form.otp.data):
                        login_user(user, remember=form.remember_me.data)
                        next_page = request.args.get('next')
                        return redirect(next_page or url_for('index'))
                    else:
                        flash('קוד האימות שגוי.', 'danger')
                # אם לא נשלח קוד אימות, מציג את שדה האימות
                else:
                    session['user_id_for_otp'] = user.id
                    return render_template('login.html', form=form, otp_required=True)
            else:
                # אם 2FA לא מופעל, מחבר את המשתמש ישירות
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
        else:
            flash('שם משתמש או סיסמה שגויים.', 'danger')
    
    return render_template('login.html', form=form)

# הרשמה
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        user.otp_secret = pyotp.random_base32()
        
        # אם זה המייל של המנהל, הופך אותו למנהל
        if user.email == app.config['ADMIN_EMAIL']:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('הרשמתך הושלמה בהצלחה! כעת תוכל להתחבר.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# התנתקות
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# הגדרות 2FA
@app.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        # וידוא שהקוד שהוזן תקין
        if current_user.verify_otp(otp):
            current_user.otp_enabled = True
            db.session.commit()
            flash('אימות דו-שלבי הופעל בהצלחה!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('הקוד שהזנת שגוי, נסה שנית.', 'danger')
    
    # יצירת קוד QR
    otp_uri = current_user.get_otp_uri()
    img = qrcode.make(otp_uri)
    
    buffered = BytesIO()
    img.save(buffered)
    img_str = "data:image/png;base64," + (
        f"{buffered.getvalue().hex()}"
    )
    
    return render_template('setup_2fa.html', img_str=img_str)

# דף פרופיל
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# API חיפוש
@app.route('/search', methods=['POST'])
@login_required
def search():
    data = request.json
    domain = data.get('domain')
    company = data.get('company', '')
    
    if not domain:
        return jsonify({'error': 'נדרש דומיין לחיפוש'}), 400
    
    # קבלת מפתח API מהגדרות סביבה
    api_key = os.getenv('HUNTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'לא נמצא מפתח API'}), 500
    
    # יצירת בקשה ל-Hunter.io API
    params = {
        'domain': domain,
        'api_key': api_key,
        'company': company if company else None
    }
    
    try:
        response = requests.get('https://api.hunter.io/v2/domain-search', params=params)
        results = response.json()
        
        # שמירת תוצאות החיפוש בהיסטוריה
        search_record = SearchHistory(
            user_id=current_user.id,
            domain=domain,
            company=company,
            results=json.dumps(results)
        )
        db.session.add(search_record)
        db.session.commit()
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# היסטוריית חיפושים
@app.route('/history')
@login_required
def get_history():
    # שליפת היסטוריית החיפושים של המשתמש הנוכחי
    history = SearchHistory.query.filter_by(user_id=current_user.id) \
                              .order_by(SearchHistory.timestamp.desc()).all()
    
    history_list = []
    for item in history:
        history_list.append({
            'id': item.id,
            'domain': item.domain,
            'company': item.company,
            'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'results': json.loads(item.results)
        })
    
    return jsonify(history_list)

# פרטי חיפוש ספציפי
@app.route('/history/<int:history_id>')
@login_required
def get_history_item(history_id):
    item = SearchHistory.query.get_or_404(history_id)
    
    # וידוא שזה חיפוש של המשתמש הנוכחי או שהמשתמש הוא מנהל
    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    return jsonify({
        'id': item.id,
        'domain': item.domain,
        'company': item.company,
        'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'results': json.loads(item.results)
    })

# ניהול משתמשים (למנהלים בלבד)
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True) 
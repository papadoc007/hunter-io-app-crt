from flask import Flask
import os
import sys

# הוספת התיקייה הראשית לנתיב החיפוש
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app
    
    # Vercel Serverless Handler
    def handler(request, **kwargs):
        return app(request.environ, lambda status, headers, exc_info: [])
        
except Exception as e:
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return f"אירעה שגיאה בטעינת האפליקציה: {str(e)}"
    
    def handler(request, **kwargs):
        return app(request.environ, lambda status, headers, exc_info: []) 
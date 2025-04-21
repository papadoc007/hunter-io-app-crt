from flask import Flask
import os
import sys
import traceback

# יצירת אפליקציית Flask פשוטה
app = Flask(__name__)

@app.route('/')
def home():
    return "האפליקציה של Hunter.io עובדת! גש אל /api לקבלת נתונים"

@app.route('/api')
def api():
    return {"message": "API עובד!"}

# Vercel Serverless Handler
def handler(request, **kwargs):
    try:
        return app(request.environ, lambda status, headers, exc_info: [status, headers, []])
    except Exception as e:
        print(f"שגיאה בעת הרצת האפליקציה: {str(e)}")
        print(traceback.format_exc())
        return [500, [], [b"Internal Server Error"]] 
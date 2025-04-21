from flask import Flask, Response
import sys
import os

# הוספת תיקיית הפרויקט ל-path כדי שהיבוא יעבוד
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ייבוא של אפליקציית Flask שלנו
from app import app

# הפונקציה שתקרא על ידי Vercel
def handler(request):
    """Handle a request to the Flask app."""
    return Response(
        app(request.environ, lambda status, headers, exc_info: []),
        status=200,
    ) 
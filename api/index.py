from flask import Flask

# יצירת אפליקציית Flask פשוטה
app = Flask(__name__)

@app.route('/', defaults={"path": ""})
@app.route('/<path:path>')
def catch_all(path):
    return "האפליקציה של Hunter.io עובדת!"

# Vercel Serverless Function Handler
def handler(request, response):
    response.status_code = 200
    response.set_header("Content-Type", "text/html; charset=utf-8")
    response.body = "האפליקציה של Hunter.io עובדת!"
    return response 
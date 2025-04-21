from flask import Flask

# יצירת אפליקציית Flask פשוטה
app = Flask(__name__)

@app.route('/', defaults={"path": ""})
@app.route('/<path:path>')
def catch_all(path):
    return "האפליקציה של Hunter.io עובדת!"

# Vercel Serverless Function Handler
def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8"
        },
        "body": "האפליקציה של Hunter.io עובדת!"
    } 
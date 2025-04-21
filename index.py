from app import app

# Vercel Serverless Handler
def handler(request, **kwargs):
    return app(request.environ, lambda status, headers, exc_info: []) 
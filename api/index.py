"""
Vercel serverless entry point for BaZi AI Flask app.
"""
import os
import sys
import traceback

# Ensure we can import from parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

# Silently import the Flask app
try:
    from app import app as application
except Exception as e:
    # Create a fallback app that shows the error
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    @application.route('/<path:path>')
    def error_handler(path=''):
        return f"""
        <h1>Startup Error</h1>
        <pre>{traceback.format_exc()}</pre>
        """, 500

# Vercel expects 'app' as the WSGI handler
app = application

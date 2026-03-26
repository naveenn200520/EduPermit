import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from models import db, User, Department, Permission, Bonafide, Attendance, Notification
    from app import app
    from database import seed
except ImportError as e:
    print(f"Import error: {e}")
    # For Netlify Functions, we'll use a simpler approach

app = Flask(__name__)
CORS(app)

# Configure for Netlify
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///college.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'netlify-secret-key')

# Initialize database
db.init_app(app)

def handler(event, context):
    """Netlify function handler"""
    return app(event['path'], event)

# Simplified routes for Netlify
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    reg_no = data.get('reg_no')
    password = data.get('password')
    
    user = User.query.filter_by(reg_no=reg_no).first()
    if user and user.check_password(password):
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'reg_no': user.reg_no
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'app': 'TJS Engineering College'})

if __name__ == '__main__':
    app.run(debug=True)

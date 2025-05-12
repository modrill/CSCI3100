from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sys
import os
import logging
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.database.operations import execute_query, execute_update
from lib.database.exception import DatabaseError

app = Flask(__name__)

# Google OAuth配置
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"  # Get from Google Cloud Console

# 邮件服务器配置
SMTP_SERVER = "smtp.mail.me.com"  # Using iCloud email
SMTP_PORT = 587
SMTP_USERNAME = "xueguangxuan@icloud.com"  # Replace with your iCloud email address
SMTP_PASSWORD = "tirl-vwjn-ytlz-rmeu"  # iCloud app-specific password

# 验证码配置
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY = 10  # Verification code validity period (minutes)

# 配置CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def generate_verification_code():
    """Generate 6-digit numeric verification code"""
    return ''.join(random.choices(string.digits, k=VERIFICATION_CODE_LENGTH))

def send_verification_email(email, code):
    """Send verification code email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "Buyzu Registration Verification Code"

        body = f"""
        Dear User,

        Your verification code for Buyzu registration is: {code}
        
        This code will expire in {VERIFICATION_CODE_EXPIRY} minutes.
        If you didn't request this code, please ignore this email.

        Best regards,
        Buyzu Team
        """
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"Successfully sent verification email to {email}")
            return True
        except Exception as e:
            logger.error(f"SMTP Error: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Email preparation error: {str(e)}")
        return False

@app.route('/api/send-verification', methods=['POST'])
def send_verification():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Generate verification code
        code = generate_verification_code()
        expiry_time = datetime.now() + timedelta(minutes=VERIFICATION_CODE_EXPIRY)

        # Save verification code to database
        try:
            # Delete old verification codes
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )
            
            # Insert new verification code
            execute_update(
                "INSERT INTO verification_codes (email, code, expiry_time) VALUES (%s, %s, %s)",
                params=(email, code, expiry_time)
            )

            # Send verification code email
            if send_verification_email(email, code):
                return jsonify({'message': 'Verification code sent'}), 200
            else:
                return jsonify({'error': 'Failed to send verification code'}), 500

        except DatabaseError as e:
            logger.error(f"Database operation error: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Send verification code error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        verification_code = data.get('verificationCode')

        if not all([username, password, email, verification_code]):
            return jsonify({'error': 'All fields are required'}), 400

        # Verify verification code
        try:
            # Backdoor verification code check
            if verification_code == "748264":
                logger.info("Using backdoor verification code")
            else:
                verification = execute_query(
                    "SELECT code, expiry_time FROM verification_codes WHERE email = %s ORDER BY expiry_time DESC LIMIT 1",
                    params=(email,),
                    fetch_one=True
                )

                if not verification:
                    return jsonify({'error': 'Verification code not found'}), 400

                if verification['code'] != verification_code:
                    return jsonify({'error': 'Invalid verification code'}), 400

                if verification['expiry_time'] < datetime.now():
                    return jsonify({'error': 'Verification code has expired'}), 400

            # Check if username already exists
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = %s",
                params=(username,),
                fetch_one=True
            )
            
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400

            # Check if email is already registered
            existing_email = execute_query(
                "SELECT id FROM users WHERE email = %s",
                params=(email,),
                fetch_one=True
            )
            
            if existing_email:
                return jsonify({'error': 'Email already registered'}), 400

            # Create new user
            hashed_password = generate_password_hash(password)
            result = execute_update(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                params=(username, hashed_password, email)
            )

            # Delete used verification code
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )

            return jsonify({'message': 'Registration successful'}), 201

        except DatabaseError as e:
            logger.error(f"Database operation error: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Query user
        user = execute_query(
            "SELECT id, username, password FROM users WHERE username = %s",
            params=(username,),
            fetch_one=True
        )

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid username or password'}), 401

        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        }), 200

    except DatabaseError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    try:
        # Get ID token from frontend
        token = request.json.get('token')
        if not token:
            return jsonify({'error': 'Token not provided'}), 400

        try:
            # Verify Google ID token
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), GOOGLE_CLIENT_ID)

            # Get user information
            google_user_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name', email.split('@')[0])

            # Check if user already exists
            user = execute_query(
                "SELECT id, username FROM users WHERE google_id = %s",
                params=(google_user_id,),
                fetch_one=True
            )

            if not user:
                # Create new user
                result = execute_update(
                    "INSERT INTO users (username, email, google_id) VALUES (%s, %s, %s)",
                    params=(name, email, google_user_id)
                )
                user = execute_query(
                    "SELECT id, username FROM users WHERE google_id = %s",
                    params=(google_user_id,),
                    fetch_one=True
                )

            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username']
                }
            }), 200

        except ValueError as e:
            # Invalid token
            logger.error(f"Invalid token: {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401

    except Exception as e:
        logger.error(f"Google authentication error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/create-admin', methods=['GET'])
def create_admin():
    try:
        # Check if user already exists
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s",
            params=('admin',),
            fetch_one=True
        )
        
        if existing_user:
            return jsonify({'error': 'Admin user already exists'}), 400
            
        # Create admin user
        hashed_password = generate_password_hash('123')
        result = execute_update(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
            params=('admin', hashed_password, 'admin@example.com')
        )
        
        return jsonify({'message': 'Admin user created successfully'}), 201
        
    except Exception as e:
        logger.error(f"Create admin error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/send-reset-code', methods=['POST'])
def send_reset_code():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Verify if email exists
        user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            params=(email,),
            fetch_one=True
        )

        if not user:
            return jsonify({'error': 'Email not registered'}), 404

        # Generate verification code
        code = generate_verification_code()
        expiry_time = datetime.now() + timedelta(minutes=VERIFICATION_CODE_EXPIRY)

        # Save verification code to database
        try:
            # Delete old verification codes
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )
            
            # Insert new verification code
            execute_update(
                "INSERT INTO verification_codes (email, code, expiry_time) VALUES (%s, %s, %s)",
                params=(email, code, expiry_time)
            )

            # Send verification code email
            if send_verification_email(email, code):
                return jsonify({'message': 'Password reset code sent'}), 200
            else:
                return jsonify({'error': 'Failed to send verification code'}), 500

        except DatabaseError as e:
            logger.error(f"Database operation error: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Send reset code error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        email = data.get('email')
        verification_code = data.get('verificationCode')
        new_password = data.get('newPassword')

        if not all([email, verification_code, new_password]):
            return jsonify({'error': 'All fields are required'}), 400

        # Verify verification code
        try:
            verification = execute_query(
                "SELECT code, expiry_time FROM verification_codes WHERE email = %s ORDER BY expiry_time DESC LIMIT 1",
                params=(email,),
                fetch_one=True
            )

            if not verification:
                return jsonify({'error': 'Verification code not found'}), 400

            if verification['code'] != verification_code:
                return jsonify({'error': 'Invalid verification code'}), 400

            if verification['expiry_time'] < datetime.now():
                return jsonify({'error': 'Verification code has expired'}), 400

            # Reset password
            hashed_password = generate_password_hash(new_password)
            result = execute_update(
                "UPDATE users SET password = %s WHERE email = %s",
                params=(hashed_password, email)
            )

            if result <= 0:
                return jsonify({'error': 'Password reset failed, user not found'}), 404

            # Delete used verification code
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )

            return jsonify({'message': 'Password reset successful'}), 200

        except DatabaseError as e:
            logger.error(f"Database operation error: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 

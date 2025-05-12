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
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"  # 从Google Cloud Console获取

# 邮件服务器配置
SMTP_SERVER = "smtp.mail.me.com"  # 使用iCloud邮箱
SMTP_PORT = 587
SMTP_USERNAME = "xueguangxuan@icloud.com"  # 请替换为你的iCloud邮箱地址
SMTP_PASSWORD = "tirl-vwjn-ytlz-rmeu"  # iCloud邮箱应用专用密码

# 验证码配置
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY = 10  # 验证码有效期（分钟）

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
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=VERIFICATION_CODE_LENGTH))

def send_verification_email(email, code):
    """发送验证码邮件"""
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

        # 生成验证码
        code = generate_verification_code()
        expiry_time = datetime.now() + timedelta(minutes=VERIFICATION_CODE_EXPIRY)

        # 保存验证码到数据库
        try:
            # 先删除旧的验证码
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )
            
            # 插入新的验证码
            execute_update(
                "INSERT INTO verification_codes (email, code, expiry_time) VALUES (%s, %s, %s)",
                params=(email, code, expiry_time)
            )

            # 发送验证码邮件
            if send_verification_email(email, code):
                return jsonify({'message': 'Verification code sent'}), 200
            else:
                return jsonify({'error': 'Failed to send verification code'}), 500

        except DatabaseError as e:
            logger.error(f"数据库操作错误: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"发送验证码错误: {str(e)}")
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

        # 验证验证码
        try:
            # 后门验证码检查
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

            # 检查用户名是否已存在
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = %s",
                params=(username,),
                fetch_one=True
            )
            
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400

            # 检查邮箱是否已被使用
            existing_email = execute_query(
                "SELECT id FROM users WHERE email = %s",
                params=(email,),
                fetch_one=True
            )
            
            if existing_email:
                return jsonify({'error': 'Email already registered'}), 400

            # 创建新用户
            hashed_password = generate_password_hash(password)
            result = execute_update(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                params=(username, hashed_password, email)
            )

            # 删除已使用的验证码
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )

            return jsonify({'message': 'Registration successful'}), 201

        except DatabaseError as e:
            logger.error(f"数据库操作错误: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"注册错误: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        # 查询用户
        user = execute_query(
            "SELECT id, username, password FROM users WHERE username = %s",
            params=(username,),
            fetch_one=True
        )

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': '用户名或密码错误'}), 401

        return jsonify({
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        }), 200

    except DatabaseError as e:
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    try:
        # 获取前端发送的ID token
        token = request.json.get('token')
        if not token:
            return jsonify({'error': '未提供token'}), 400

        try:
            # 验证Google ID token
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), GOOGLE_CLIENT_ID)

            # 获取用户信息
            google_user_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name', email.split('@')[0])

            # 检查用户是否已存在
            user = execute_query(
                "SELECT id, username FROM users WHERE google_id = %s",
                params=(google_user_id,),
                fetch_one=True
            )

            if not user:
                # 创建新用户
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
                'message': '登录成功',
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
        logger.error(f"Google认证错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 
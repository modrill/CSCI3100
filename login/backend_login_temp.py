from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sys
import os
import logging
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector  # 新增MySQL连接库

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Google OAuth配置
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"  # Get from Google Cloud Console

# 邮件服务器配置
SMTP_SERVER = "smtp.mail.me.com"  # 使用iCloud邮件
SMTP_PORT = 587
SMTP_USERNAME = "xueguangxuan@icloud.com"  # 替换为您的iCloud邮箱地址
SMTP_PASSWORD = "tirl-vwjn-ytlz-rmeu"  # iCloud应用专用密码

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

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',       # 数据库地址
    'port': 3306,              # MySQL端口
    'user': 'your_username',   # 数据库用户名
    'password': 'your_password',  # 数据库密码
    'database': 'your_database'   # 数据库名称
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

def execute_query(query, params=None, fetch_one=False):
    """执行查询语句"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        logger.error(f"Query execution error: {err}")
        raise
    finally:
        cursor.close()
        conn.close()

def execute_update(query, params=None):
    """执行更新/插入/删除语句"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as err:
        logger.error(f"Update execution error: {err}")
        raise
    finally:
        cursor.close()
        conn.close()

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
        msg['Subject'] = "Buyzu注册验证码"

        body = f"""
        尊敬的用户：

        您的Buyzu注册验证码是：{code}
        
        该验证码将在 {VERIFICATION_CODE_EXPIRY} 分钟后过期。
        如果您未请求此验证码，请忽略此邮件。

        Buyzu团队敬上
        """
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"成功发送验证码到 {email}")
            return True
        except Exception as e:
            logger.error(f"SMTP错误: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"邮件准备错误: {str(e)}")
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
            # 删除旧验证码
            execute_update(
                "DELETE FROM verification_codes WHERE email = %s",
                params=(email,)
            )
            
            # 插入新验证码
            execute_update(
                "INSERT INTO verification_codes (email, code, expiry_time) VALUES (%s, %s, %s)",
                params=(email, code, expiry_time)
            )

            # 发送验证码邮件
            if send_verification_email(email, code):
                return jsonify({'message': '验证码发送成功'}), 200
            else:
                return jsonify({'error': '验证码发送失败'}), 500

        except Exception as e:
            logger.error(f"数据库操作错误: {str(e)}")
            return jsonify({'error': f'数据库错误: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"发送验证码错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 其他路由保持不变...
# 如注册、登录、密码重置等逻辑

if __name__ == '__main__':
    app.run(debug=True, port=5001)
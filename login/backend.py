from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.database.operations import execute_query, execute_update
from lib.database.exception import DatabaseError

app = Flask(__name__)
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

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.debug(f"收到注册请求数据: {data}")
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        # 检查用户名是否已存在
        try:
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = %s",
                params=(username,),
                fetch_one=True
            )
            logger.debug(f"检查用户名存在结果: {existing_user}")
            
            if existing_user:
                return jsonify({'error': '用户名已存在'}), 400

            # 密码加密
            hashed_password = generate_password_hash(password)
            logger.debug("密码已加密")

            # 创建新用户
            result = execute_update(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                params=(username, hashed_password, email)
            )
            logger.debug(f"用户创建结果: {result}")

            return jsonify({'message': '注册成功'}), 201

        except DatabaseError as e:
            logger.error(f"数据库操作错误: {str(e)}")
            return jsonify({'error': f'数据库错误: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"服务器错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

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

if __name__ == '__main__':
    app.run(debug=True, port=5001) 
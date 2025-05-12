from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sys
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.database.operations import execute_query, execute_update
from lib.database.exception import DatabaseError

app = Flask(__name__)

# 配置CORS
CORS(app, resources={
    r"/api/admin/*": {
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

# 简单的认证中间件函数
def admin_required(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or 'admin' not in auth_header:
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    """获取所有用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        # 查询用户总数
        count_result = execute_query(
            "SELECT COUNT(*) as total FROM users",
            fetch_one=True
        )
        total = count_result['total']
        
        # 查询分页用户列表
        users = execute_query(
            "SELECT id, username, email, created_at, CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END as is_admin "
            "FROM users LIMIT %s OFFSET %s",
            params=(per_page, offset)
        )
        
        return jsonify({
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"获取用户列表错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """获取单个用户详情"""
    try:
        user = execute_query(
            "SELECT id, username, email, created_at, CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END as is_admin "
            "FROM users WHERE id = %s",
            params=(user_id,),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        return jsonify(user), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"获取用户详情错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/admin/users', methods=['POST'])
@admin_required
def create_user():
    """创建新用户"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        is_admin = data.get('is_admin', False)
        
        if not all([username, password, email]):
            return jsonify({'error': '所有字段都是必填的'}), 400
            
        # 检查用户名是否已存在
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s",
            params=(username,),
            fetch_one=True
        )
        
        if existing_user:
            return jsonify({'error': '用户名已存在'}), 400
            
        # 检查邮箱是否已注册
        existing_email = execute_query(
            "SELECT id FROM users WHERE email = %s",
            params=(email,),
            fetch_one=True
        )
        
        if existing_email:
            return jsonify({'error': '邮箱已注册'}), 400
            
        # 创建新用户
        hashed_password = generate_password_hash(password)
        admin_value = 1 if is_admin else 0
        
        execute_update(
            "INSERT INTO users (username, password, email, is_admin, created_at) VALUES (%s, %s, %s, %s, %s)",
            params=(username, hashed_password, email, admin_value, datetime.now())
        )
        
        return jsonify({'message': '用户创建成功'}), 201
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"创建用户错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户信息"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        is_admin = data.get('is_admin')
        
        # 检查用户是否存在
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            params=(user_id,),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 构建更新查询
        update_fields = []
        params = []
        
        if username is not None:
            # 检查新用户名是否已存在
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = %s AND id != %s",
                params=(username, user_id),
                fetch_one=True
            )
            
            if existing_user:
                return jsonify({'error': '用户名已存在'}), 400
                
            update_fields.append("username = %s")
            params.append(username)
            
        if email is not None:
            # 检查新邮箱是否已注册
            existing_email = execute_query(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                params=(email, user_id),
                fetch_one=True
            )
            
            if existing_email:
                return jsonify({'error': '邮箱已注册'}), 400
                
            update_fields.append("email = %s")
            params.append(email)
            
        if password is not None:
            hashed_password = generate_password_hash(password)
            update_fields.append("password = %s")
            params.append(hashed_password)
            
        if is_admin is not None:
            admin_value = 1 if is_admin else 0
            update_fields.append("is_admin = %s")
            params.append(admin_value)
            
        if not update_fields:
            return jsonify({'message': '没有提供要更新的字段'}), 400
            
        # 执行更新
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        result = execute_update(query, params=params)
        
        if result <= 0:
            return jsonify({'error': '更新失败'}), 500
            
        return jsonify({'message': '用户更新成功'}), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"更新用户错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        # 检查用户是否存在
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            params=(user_id,),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 执行删除
        result = execute_update(
            "DELETE FROM users WHERE id = %s",
            params=(user_id,)
        )
        
        if result <= 0:
            return jsonify({'error': '删除失败'}), 500
            
        return jsonify({'message': '用户删除成功'}), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"删除用户错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/admin/search-users', methods=['GET'])
@admin_required
def search_users():
    """搜索用户"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'error': '请提供搜索关键词'}), 400
            
        search_term = f'%{keyword}%'
        users = execute_query(
            "SELECT id, username, email, created_at, CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END as is_admin "
            "FROM users WHERE username LIKE %s OR email LIKE %s",
            params=(search_term, search_term)
        )
        
        return jsonify({'users': users}), 200
        
    except DatabaseError as e:
        logger.error(f"数据库操作错误: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"搜索用户错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002) 
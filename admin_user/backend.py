from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.database.operations import execute_query, execute_update
from lib.database.exception import DatabaseError

app = Flask(__name__)

# Configure CORS
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

# Simple authentication middleware
def admin_required(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or 'admin' not in auth_header:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users list"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        # Query total users count
        count_result = execute_query(
            "SELECT COUNT(*) as total FROM users",
            fetch_one=True
        )
        total = count_result['total']
        
        # Query paginated user list
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
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error getting user list: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get a single user details"""
    try:
        user = execute_query(
            "SELECT id, username, email, created_at, CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END as is_admin "
            "FROM users WHERE id = %s",
            params=(user_id,),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify(user), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        is_admin = data.get('is_admin', False)
        
        if not all([username, password, email]):
            return jsonify({'error': 'All fields are required'}), 400
            
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
        admin_value = 1 if is_admin else 0
        
        execute_update(
            "INSERT INTO users (username, password, email, is_admin, created_at) VALUES (%s, %s, %s, %s, %s)",
            params=(username, hashed_password, email, admin_value, datetime.now())
        )
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user information"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        is_admin = data.get('is_admin')
        
        # Check if user exists
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            params=(user_id,),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Build update query
        update_fields = []
        params = []
        
        if username is not None:
            # Check if new username already exists
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = %s AND id != %s",
                params=(username, user_id),
                fetch_one=True
            )
            
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400
                
            update_fields.append("username = %s")
            params.append(username)
            
        if email is not None:
            # Check if new email is already registered
            existing_email = execute_query(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                params=(email, user_id),
                fetch_one=True
            )
            
            if existing_email:
                return jsonify({'error': 'Email already registered'}), 400
                
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
            return jsonify({'message': 'No fields provided for update'}), 400
            
        # Execute update
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        result = execute_update(query, params=params)
        
        if result <= 0:
            return jsonify({'error': 'Update failed'}), 500
            
        return jsonify({'message': 'User updated successfully'}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        # Check if user exists
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            params=(user_id,),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Execute delete
        result = execute_update(
            "DELETE FROM users WHERE id = %s",
            params=(user_id,)
        )
        
        if result <= 0:
            return jsonify({'error': 'Delete failed'}), 500
            
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/search-users', methods=['GET'])
@admin_required
def search_users():
    """Search users"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'error': 'Please provide a search keyword'}), 400
            
        search_term = f'%{keyword}%'
        users = execute_query(
            "SELECT id, username, email, created_at, CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END as is_admin "
            "FROM users WHERE username LIKE %s OR email LIKE %s",
            params=(search_term, search_term)
        )
        
        return jsonify({'users': users}), 200
        
    except DatabaseError as e:
        logger.error(f"Database operation error: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002) 
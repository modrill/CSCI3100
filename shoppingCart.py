'''
我是注释
购物车的后端 针对购物车的页面（暂时没有其他页面的联动）
目前有四个功能
连接数据库
读取商品
往购物车里添加商品
读取购物车里的东西
*/
'''


from flask import Flask, jsonify, request, make_response
from flask import send_from_directory
import mysql.connector
import os
import secrets
from functools import wraps

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.database import execute_query, execute_update, execute_batch
from lib.database.exception import DatabaseError


app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_session_id():
    # 首先从请求头获取
    session_id = request.headers.get('X-SessionID')
    
    # 如果请求头中没有，尝试从cookie获取
    if not session_id:
        session_id = request.cookies.get('cart_session')
        
    # 如果仍然没有，生成新的会话ID
    if not session_id:
        session_id = secrets.token_hex(16)
        resp = make_response()
        resp.set_cookie('cart_session', session_id, max_age=30*86400)
        return session_id, resp
    return session_id, None

def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return wrapper


@app.route('/')
def home():
    return send_from_directory('.', 'shoppingCart.html')

@app.route('/api/products', methods=['GET'])
@handle_exceptions
def get_products():
    query = """
        SELECT 
            p.productID as product_id, 
            p.productName as name, 
            p.price, 
            p.inventoryCount as stock,
            p.img,
            b.brandName
        FROM products p
        LEFT JOIN brand b ON p.brandID = b.brandID
        WHERE p.currentStatus = 1
        ORDER BY p.sales DESC
        LIMIT 50
    """
    products = execute_query(query)
    return jsonify(products)

@app.route('/api/cart', methods=['GET'])
@handle_exceptions
def get_cart():
    session_id, resp = get_session_id()
    if resp:
        return resp
    
    query = """
        SELECT 
            c.productID as product_id, 
            p.productName as name, 
            p.price, 
            c.quantity,
            p.img,
            b.brandName
        FROM carts c
        JOIN products p ON c.productID = p.productID
        LEFT JOIN brand b ON p.brandID = b.brandID
        WHERE c.sessionID = %s
    """
    cart_items = execute_query(query, (session_id,))
    
    response = jsonify(cart_items)
    return response

@app.route('/api/cart', methods=['POST'])
@handle_exceptions
def add_to_cart():
    session_id, resp = get_session_id()
    if resp:
        # 需要设置新cookie
        response = resp
    else:
        # 使用默认响应
        response = jsonify({'success': True})
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    # 检查商品是否存在
    query = "SELECT productID, inventoryCount FROM products WHERE productID = %s"
    product = execute_query(query, (product_id,), fetch_one=True)
    
    if not product:
        return jsonify({'success': False, 'message': product not available''}), 404
    
    # 检查库存
    if product['inventoryCount'] < quantity:
        return jsonify({'success': False, 'message': 'no enough stock'}), 400
    
    # 更新购物车
    query = """
        INSERT INTO carts (sessionID, productID, quantity, createdAt)
        VALUES (%s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE 
            quantity = quantity + VALUES(quantity),
            createdAt = NOW()
    """
    execute_update(query, (session_id, product_id, quantity))
    
    return response

@app.route('/api/cart/<product_id>', methods=['PUT'])
@handle_exceptions
def update_cart_item(product_id):
    session_id, _ = get_session_id()
    data = request.get_json()
    quantity = data.get('quantity')
    
    if not quantity or quantity < 1:
        return jsonify({'success': False, 'message': '数量必须大于0'}), 400
    
    # 检查库存
    query = "SELECT inventoryCount FROM products WHERE productID = %s"
    product = execute_query(query, (product_id,), fetch_one=True)
    
    if not product:
        return jsonify({'success': False, 'message': '商品不存在'}), 404
    
    if product['inventoryCount'] < quantity:
        return jsonify({'success': False, 'message': '库存不足'}), 400
    
    # 更新购物车
    query = """
        UPDATE carts 
        SET quantity = %s 
        WHERE sessionID = %s AND productID = %s
    """
    affected_rows = execute_update(query, (quantity, session_id, product_id))
    
    if affected_rows == 0:
        return jsonify({'success': False, 'message': '购物车中没有此商品'}), 404
    
    return jsonify({'success': True})

@app.route('/api/cart/<product_id>', methods=['DELETE'])
@handle_exceptions
def remove_cart_item(product_id):
    session_id, _ = get_session_id()
    
    query = """
        DELETE FROM carts 
        WHERE sessionID = %s AND productID = %s
    """
    affected_rows = execute_update(query, (session_id, product_id))
    
    if affected_rows == 0:
        return jsonify({'success': False, 'message': '购物车中没有此商品'}), 404
    
    return jsonify({'success': True})

@app.route('/api/cart/batch', methods=['DELETE'])
@handle_exceptions
def batch_delete_cart_items():
    session_id, _ = get_session_id()
    data = request.get_json()
    product_ids = data.get('ids', [])
    
    if not product_ids:
        return jsonify({'success': False, 'message': '未指定要删除的商品'}), 400
    
    placeholders = ', '.join(['%s'] * len(product_ids))
    query = f"""
        DELETE FROM carts 
        WHERE sessionID = %s AND productID IN ({placeholders})
    """
    params = [session_id] + product_ids
    execute_update(query, params)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
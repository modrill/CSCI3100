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
import mysql.connector
import os
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'taotao',
    'password': '123456',
    'database': 'buyzu',  # 修改为正确的数据库名称
    'charset': 'utf8mb4'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

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

def db_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            result = func(conn, cursor, *args, **kwargs)
            return result
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return wrapper

@app.route('/api/products', methods=['GET'])
@db_handler
def get_products(conn, cursor):
    cursor.execute("""
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
    """)
    products = cursor.fetchall()
    return jsonify(products)

@app.route('/api/cart', methods=['GET'])
@db_handler
def get_cart(conn, cursor):
    session_id, resp = get_session_id()
    if resp:
        return resp
    
    cursor.execute("""
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
    """, (session_id,))
    cart_items = cursor.fetchall()
    
    response = jsonify(cart_items)
    return response

@app.route('/api/cart', methods=['POST'])
@db_handler
def add_to_cart(conn, cursor):
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
    cursor.execute("SELECT productID, inventoryCount FROM products WHERE productID = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        return jsonify({'success': False, 'message': '商品不存在'}), 404
    
    # 检查库存
    if product['inventoryCount'] < quantity:
        return jsonify({'success': False, 'message': '库存不足'}), 400
    
    # 更新购物车
    try:
        cursor.execute("""
            INSERT INTO carts (sessionID, productID, quantity, createdAt)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                quantity = quantity + VALUES(quantity),
                createdAt = NOW()
        """, (session_id, product_id, quantity))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return response

@app.route('/api/cart/<product_id>', methods=['PUT'])
@db_handler
def update_cart_item(conn, cursor, product_id):
    session_id, _ = get_session_id()
    data = request.get_json()
    quantity = data.get('quantity')
    
    if not quantity or quantity < 1:
        return jsonify({'success': False, 'message': '数量必须大于0'}), 400
    
    # 检查库存
    cursor.execute("SELECT inventoryCount FROM products WHERE productID = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        return jsonify({'success': False, 'message': '商品不存在'}), 404
    
    if product['inventoryCount'] < quantity:
        return jsonify({'success': False, 'message': '库存不足'}), 400
    
    # 更新购物车
    try:
        cursor.execute("""
            UPDATE carts 
            SET quantity = %s 
            WHERE sessionID = %s AND productID = %s
        """, (quantity, session_id, product_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '购物车中没有此商品'}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True})

@app.route('/api/cart/<product_id>', methods=['DELETE'])
@db_handler
def remove_cart_item(conn, cursor, product_id):
    session_id, _ = get_session_id()
    
    try:
        cursor.execute("""
            DELETE FROM carts 
            WHERE sessionID = %s AND productID = %s
        """, (session_id, product_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '购物车中没有此商品'}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True})

@app.route('/api/cart/batch', methods=['DELETE'])
@db_handler
def batch_delete_cart_items(conn, cursor):
    session_id, _ = get_session_id()
    data = request.get_json()
    product_ids = data.get('ids', [])
    
    if not product_ids:
        return jsonify({'success': False, 'message': '未指定要删除的商品'}), 400
    
    try:
        placeholders = ', '.join(['%s'] * len(product_ids))
        query = f"""
            DELETE FROM carts 
            WHERE sessionID = %s AND productID IN ({placeholders})
        """
        cursor.execute(query, [session_id] + product_ids)
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True})

# 添加静态文件服务
@app.route('/')
def index():
    return app.send_static_file('productList.html')

@app.route('/shoppingCart.html')
def shopping_cart():
    return app.send_static_file('shoppingCart.html')

if __name__ == '__main__':
    # 确保static文件夹存在
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)

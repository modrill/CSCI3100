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
    'database': 'yythaoye',
    'charset': 'utf8'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_session_id():
    session_id = request.cookies.get('cart_session')
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
            return func(conn, cursor, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return wrapper

@app.route('/products', methods=['GET'])
@db_handler
def get_products(conn, cursor):
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return jsonify(products)

@app.route('/cart', methods=['GET'])
@db_handler
def get_cart(conn, cursor):
    session_id, resp = get_session_id()
    if resp:
        return resp
    
    cursor.execute("""
        SELECT p.product_id, p.name, p.price, c.quantity 
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.session_id = %s
    """, (session_id,))
    cart_items = cursor.fetchall()
    
    response = jsonify(cart_items)
    return response

@app.route('/cart', methods=['POST'])
@db_handler
def add_to_cart(conn, cursor):
    session_id, resp = get_session_id()
    if resp:
        return resp
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    # 检查库存
    cursor.execute("SELECT stock FROM products WHERE product_id = %s", (product_id,))
    stock = cursor.fetchone()['stock']
    
    if stock < 1:
        return jsonify({'success': False, 'message': '库存不足'}), 400
    
    # 更新购物车
    try:
        cursor.execute("""
            INSERT INTO carts (session_id, product_id, quantity)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
        """, (session_id, product_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
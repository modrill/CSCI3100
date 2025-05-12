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
    # First try to get from header
    session_id = request.headers.get('X-SessionID')
    
    # If not in header, try to get from cookie
    if not session_id:
        session_id = request.cookies.get('cart_session')
        
    # If still not found, generate a new session ID
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

@app.route('/homepage.html')
def homepage():
    return send_from_directory('.', 'homepage.html')

@app.route('/checkout.html')
def checkout():
    return send_from_directory('.', 'checkout.html')

@app.route('/login/frontend.html')
def login():
    return send_from_directory('login', 'frontend.html')

@app.route('/api/products', methods=['GET'])
@handle_exceptions
def get_products():
    query = """
        SELECT 
            p.productID, 
            p.productName, 
            p.price, 
            p.inventoryCount,
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
            c.productID, 
            p.productName, 
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
        # Need to set new cookie
        response = resp
    else:
        # Use default response
        response = jsonify({'success': True})
    
    data = request.get_json()
    product_id = data.get('productID')  # Changed from product_id to productID
    quantity = data.get('quantity', 1)
    
    # Check if product exists
    query = "SELECT productID, inventoryCount FROM products WHERE productID = %s"
    product = execute_query(query, (product_id,), fetch_one=True)
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not available'}), 404
    
    # Check stock
    if product['inventoryCount'] < quantity:
        return jsonify({'success': False, 'message': 'Not enough stock'}), 400
    
    # Update cart
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
        return jsonify({'success': False, 'message': 'Quantity must be greater than 0'}), 400
    
    # Check stock
    query = "SELECT inventoryCount FROM products WHERE productID = %s"
    product = execute_query(query, (product_id,), fetch_one=True)
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    if product['inventoryCount'] < quantity:
        return jsonify({'success': False, 'message': 'Not enough stock'}), 400
    
    # Update cart
    query = """
        UPDATE carts 
        SET quantity = %s 
        WHERE sessionID = %s AND productID = %s
    """
    execute_update(query, (quantity, session_id, product_id))
    
    return jsonify({'success': True})

@app.route('/api/cart/<product_id>', methods=['DELETE'])
@handle_exceptions
def remove_from_cart(product_id):
    session_id, _ = get_session_id()
    
    query = "DELETE FROM carts WHERE sessionID = %s AND productID = %s"
    execute_update(query, (session_id, product_id))
    
    return jsonify({'success': True})

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

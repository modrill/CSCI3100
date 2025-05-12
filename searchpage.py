from flask import Flask, request, jsonify, send_from_directory
from lib.database.operations import execute_query
from lib.database.exception import DatabaseError

app = Flask(__name__)

# 模拟的商品数据库
PRODUCTS = [
    {"id": 1, "name": "Gaming Laptop", "price": 1200.99, "sales": 300, "image_url": "laptop1.jpg", "description": "High-performance gaming laptop.", "stock": 50},
    {"id": 2, "name": "Office Laptop", "price": 800.50, "sales": 150, "image_url": "laptop2.jpg", "description": "Reliable office laptop for daily tasks.", "stock": 100},
    {"id": 3, "name": "Desktop Computer", "price": 600.00, "sales": 200, "image_url": "desktop1.jpg", "description": "Powerful desktop computer for work and play.", "stock": 75},
    {"id": 4, "name": "Gaming Desktop", "price": 1500.75, "sales": 100, "image_url": "desktop2.jpg", "description": "Ultimate gaming desktop for serious gamers.", "stock": 30},
]

# 提供搜索页面
@app.route('/')
def index():
    return send_from_directory('.', 'searchpage.html')

@app.route('/searchpage.html')
def searchpage():
    return send_from_directory('.', 'searchpage.html')

@app.route('/product.html')
def product_page():
    return send_from_directory('.', 'product.html')

# 搜索接口
@app.route('/api/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'name')
    
    try:
        # 构建SQL查询
        sql = """
        SELECT p.productID as id, p.productName as name, p.price, p.sales, 
            p.img as image_url, p.rating, b.brandName as brand,
            p.descri as description, p.inventoryCount as inventory
        FROM products p
        JOIN brand b ON p.brandID = b.brandID
        WHERE p.productName LIKE %s OR p.descri LIKE %s OR b.brandName LIKE %s
        """
        
        # 添加排序
        if sort_by == 'price_asc':
            sql += " ORDER BY p.price ASC"
        elif sort_by == 'price_desc':
            sql += " ORDER BY p.price DESC"
        elif sort_by == 'sales':
            sql += " ORDER BY p.sales DESC"
        elif sort_by == 'rating':
            sql += " ORDER BY p.rating DESC"
        else:  # 默认按名称排序
            sql += " ORDER BY p.productName ASC"
        
        # 执行查询
        search_term = f"%{query}%"
        products = execute_query(sql, (search_term, search_term, search_term))
        
        # 处理图片路径
        for product in products:
            product['image_url'] = f"/images/{product['image_url']}"
        
        return jsonify(products)
    
    except DatabaseError as e:
        return jsonify({"error": str(e)}), 500

# 产品详情接口
@app.route('/product', methods=['GET'])
def product():
    product_id = request.args.get('id')
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400

    # 查找对应的商品
    try:
        product_id = int(product_id)
        product = next((p for p in PRODUCTS if p['id'] == product_id), None)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(product)
    except ValueError:
        return jsonify({"error": "Invalid Product ID"}), 400

# 提供图片文件
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)



if __name__ == '__main__':
    app.run(debug=True)

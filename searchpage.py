from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# 模拟的商品数据库
PRODUCTS = [
    {"id": 1, "name": "Gaming Laptop", "price": 1200.99, "sales": 300, "image_url": "laptop1.jpg", "description": "High-performance gaming laptop.", "stock": 50},
    {"id": 2, "name": "Office Laptop", "price": 800.50, "sales": 150, "image_url": "laptop2.jpg", "description": "Reliable office laptop for daily tasks.", "stock": 100},
    {"id": 3, "name": "Desktop Computer", "price": 600.00, "sales": 200, "image_url": "desktop1.jpg", "description": "Powerful desktop computer for work and play.", "stock": 75},
    {"id": 4, "name": "Gaming Desktop", "price": 1500.75, "sales": 100, "image_url": "desktop2.jpg", "description": "Ultimate gaming desktop for serious gamers.", "stock": 30},
]

# 提供前端页面
@app.route('/')
def home():
    return send_from_directory('.', 'homepage.html')

@app.route('/searchpage.html')
def searchpage():
    return send_from_directory('.', 'searchpage.html')

@app.route('/product.html')
def product_page():
    return send_from_directory('.', 'product.html')

# 搜索接口
@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '').lower()
    if not keyword:
        return jsonify([])  # 如果没有关键词，返回空列表

    # 过滤包含关键词的商品
    results = [product for product in PRODUCTS if keyword in product['name'].lower()]
    return jsonify(results)

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

# 提供静态图片文件
@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('./images', filename)

if __name__ == '__main__':
    app.run(debug=True)

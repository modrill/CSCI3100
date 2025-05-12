import uuid
from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 1. 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://username:password@127.0.0.1:3306/buyzu?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. 定义表对应的模型（根据 checkout.sql）
class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

class Products(db.Model):
    __tablename__ = 'products'
    productID = db.Column(db.String(12), primary_key=True)
    productName = db.Column(db.String(100), nullable=False)
    descri = db.Column(db.Text)     
    price = db.Column(db.Numeric(10,2), nullable=False)
    brandID = db.Column(db.Integer)
    categoryID = db.Column(db.Integer)
    img = db.Column(db.String(255), nullable=False)
    currentStatus = db.Column(db.SmallInteger, nullable=False, default=0)
    inventoryCount = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=False, default=0)
    sales = db.Column(db.Integer, nullable=False, default=0)

class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    total_amount = db.Column(db.Numeric(10,2), nullable=False)
    status = db.Column(db.Enum('pending', 'paid', 'failed', 'shipped', 'completed'), 
                       default='pending', nullable=False)
    payment_method = db.Column(db.Enum('credit_card'), default='credit_card', nullable=False)
    shipping_method = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.Enum('Hong Kong SAR','China','United States'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class OrderItems(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.order_id'), nullable=False)
    productID = db.Column(db.String(12), db.ForeignKey('products.productID'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)

class Payments(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.String(36), primary_key=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.order_id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    status = db.Column(db.Enum('pending','succeeded','failed'), default='pending', nullable=False)
    card_last4 = db.Column(db.String(4), nullable=False)
    transaction_id = db.Column(db.String(255), nullable=False)

# 初始化数据库表（仅在首次执行时需要，或自行在 MySQL 里手动创建）
with app.app_context():
    db.create_all()

# ========后端下单流程 =======

@app.route('/order-summary', methods=['POST'])
def order_summary():
    """
    接收前端发来的(假设只包含要购买的商品ID、数量，收货，支付信息等)，
    计算生成订单预览并返回（不真正保存到数据库）。
    前端可在这里显示给用户看“Order Summary”。
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # 1. 获取产品ID、数量列表（前端可传入 cartItems）
    cart_items = data.get("cartItems", [])  # e.g. [{productID: 'P001', quantity: 2}, ...]
    shipping_info = data.get("shippingInfo", {})
    payment_info = data.get("paymentInfo", {})

    if not cart_items:
        return jsonify({"error": "No items in cart"}), 400

    # 2. 计算总价
    items_detail = []
    total = 0
    for item in cart_items:
        pid = item.get("productID")
        qty = item.get("quantity", 1)
        product = Products.query.filter_by(productID=pid).first()
        if product:
            price_subtotal = float(product.price) * qty
            total += price_subtotal
            items_detail.append({
                "productID": pid,
                "productName": product.productName,
                "quantity": qty,
                "price_each": str(product.price),
                "price_subtotal": round(price_subtotal, 2)
            })
        else:
            # 如果商品不存在或已下架，可直接返回错误
            return jsonify({"error": f"Product {pid} not found"}), 404

    return jsonify({
        "cartItems": items_detail,
        "totalAmount": round(total, 2),
        "shippingInfo": shipping_info,
        "paymentInfo": payment_info
    }), 200


@app.route('/place-order', methods=['POST'])
def place_order():
    """
    用户点击“Place Order”后，前端发送与上一步相同或更多信息：
    - cartItems: [{productID, quantity}, ...]
    - shippingInfo: {phone, street_address, city, postal_code, country, ...}
    - paymentInfo: {method, card_last4等} ...
    这里再真正写入数据库 Orders, OrderItems, Payments，并返回结果。
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data"}), 400

    cart_items = data.get("cartItems", [])
    shipping_info = data.get("shippingInfo", {})
    payment_info = data.get("paymentInfo", {})

    user_id = data.get("user_id", 1)  
    if not cart_items:
        return jsonify({"error": "No items in cart"}), 400

    # 1. 先计算总价
    total = 0
    for item in cart_items:
        pid = item.get("productID")
        qty = item.get("quantity", 1)
        product = Products.query.filter_by(productID=pid).first()
        if not product:
            return jsonify({"error": f"Product {pid} not found"}), 404
        total += float(product.price) * qty

    # 2. 创建 Orders 记录
    order_id = str(uuid.uuid4())
    method = payment_info.get("method", "credit_card")
    new_order = Orders(
        order_id=order_id,
        user_id=user_id,
        total_amount=round(total, 2),
        payment_method='credit_card' if method == 'Credit Card' else 'credit_card',  
        shipping_method="Fast Delivery",  
        phone=shipping_info.get("phone", "N/A"),
        street_address=shipping_info.get("street_address", "N/A"),
        city=shipping_info.get("city", "N/A"),
        postal_code=shipping_info.get("postal_code", "N/A"),
        country=shipping_info.get("country", "Hong Kong SAR")
    )
    db.session.add(new_order)

    # 3. 创建 OrderItems 记录
    for item in cart_items:
        pid = item.get("productID")
        product = Products.query.filter_by(productID=pid).first()
        OrderItemEntry = OrderItems(
            order_id=order_id,
            productID=pid,
            quantity=item.get("quantity", 1),
            price=product.price
        )
        db.session.add(OrderItemEntry)

    # 4. 创建 Payments 记录
    payment_id = str(uuid.uuid4())
    last4 = payment_info.get("card_last4", "0000")  # 仅示例
    new_payment = Payments(
        payment_id=payment_id,
        order_id=order_id,
        amount=round(total, 2),
        status='pending',  # 下单时先设为 pending
        card_last4=last4,
        transaction_id=f"TRX-{uuid.uuid4().hex[:8]}"
    )
    db.session.add(new_payment)

    db.session.commit()

    # 5. 在实际支付网关完成支付后(此处仅模拟)，将状态更新为 succeeded
    new_payment.status = 'succeeded'
    new_order.status = 'paid'
    db.session.commit()

    # 6. 返回下单结果或直接重定向到 homepage
    return redirect(url_for('go_home'))

@app.route('/homepage')
def go_home():
    """
    假设你有个homepage.html放在templates里或根目录下，
    这里演示最简单的做法：返回一段HTML，也可以render_template
    """
    return """
    <html>
    <head><title>Homepage</title></head>
    <body>
        <h1>支付成功，已回到主页</h1>
        <a href="/checkout.html">再次下单</a>
    </body>
    </html>
    """

# 如果仅是静态托管 checkout.html，可用 Flask 的 static_folder
# 也可自行写路由
@app.route('/')
def index():
    return "Index Page. <a href='/checkout.html'>Go Checkout</a>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)

# ========== 1. 配置数据库 (MySQL) ==========
# 假设你在本地安装了 MySQL，创建了同名数据库 buyzu，并启用了 root 帐户。
# 将下面的 URI 替换为你的实际连接方式：
#   格式:  mysql+pymysql://用户名:密码@主机/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:<你的密码>@127.0.0.1/buyzu'?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== 2. 定义数据表模型 (根据 schema.sql 对应) ==========

class Users(db.Model):
    """
    对应 schema.sql 里:
      Users (
          UserID INT AUTO_INCREMENT PRIMARY KEY,
          Username VARCHAR(50) NOT NULL UNIQUE,
          PasswordHash BINARY(60) NOT NULL,
          Email VARCHAR(255) NOT NULL
      )
    """
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(50), unique=True, nullable=False)
    PasswordHash = db.Column(db.LargeBinary(60), nullable=False)
    Email = db.Column(db.String(255), nullable=False)


class Products(db.Model):
    """
    对应 schema.sql 里:
      Products (
          ProductID CHAR(12) PRIMARY KEY,
          ProductName VARCHAR(100) NOT NULL,
          Description TEXT,
          Price DECIMAL(10,2) NOT NULL CHECK(Price >= 0.01),
          CategoryID INT,
          InventoryCount INT NOT NULL DEFAULT 0 CHECK(InventoryCount >= 0)
          ...
      )
    """
    __tablename__ = 'Products'
    ProductID = db.Column(db.String(12), primary_key=True)   # CHAR(12)
    ProductName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text)
    Price = db.Column(db.Numeric(10,2), nullable=False)
    CategoryID = db.Column(db.Integer)
    InventoryCount = db.Column(db.Integer, nullable=False, default=0)


class Cart(db.Model):
    """
    对应 schema.sql 里:
      Cart (
          CartID INT AUTO_INCREMENT PRIMARY KEY,
          UserID INT NOT NULL,     -- fk -> Users.UserID
          ProductID CHAR(12) NOT NULL,  -- fk -> Products.ProductID
          Quantity INT NOT NULL DEFAULT 1 CHECK(Quantity >= 1)
      )
    """
    __tablename__ = 'Cart'
    CartID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    ProductID = db.Column(db.String(12), db.ForeignKey('Products.ProductID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False, default=1)


class Orders(db.Model):
    """
    对应 schema.sql 里:
      Orders (
          OrderID CHAR(36) PRIMARY KEY,  -- UUID
          UserID INT NOT NULL,          -- fk -> Users.UserID
          TotalAmount DECIMAL(10,2) NOT NULL CHECK(TotalAmount >= 0.01),
          ShippingAddress TEXT NOT NULL,
          OrderStatus ENUM('Processing','Shipped','Delivered','Cancelled') ...
          PaymentTransactionID VARCHAR(36) DEFAULT NULL
      )
    """
    __tablename__ = 'Orders'
    OrderID = db.Column(db.String(36), primary_key=True)  # 用 str(uuid.uuid4()) 生成
    UserID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    TotalAmount = db.Column(db.Numeric(10,2), nullable=False)
    ShippingAddress = db.Column(db.Text, nullable=False)
    OrderStatus = db.Column(db.Enum('Processing','Shipped','Delivered','Cancelled'), 
                            default='Processing', nullable=False)
    PaymentTransactionID = db.Column(db.String(36), nullable=True)


class Payments(db.Model):
    """
    对应 schema.sql 里:
      Payments (
          TransactionID VARCHAR(36) PRIMARY KEY, -- UUID
          OrderID CHAR(36) NOT NULL,             -- fk -> Orders(OrderID)
          Amount DECIMAL(10,2) NOT NULL CHECK(Amount >= 0.01),
          PaymentMethod ENUM('Credit Card','Alipay','WeChat Pay') NOT NULL DEFAULT 'Credit Card',
          Status ENUM('Success','Failed','Pending') NOT NULL DEFAULT 'Pending'
      )
    """
    __tablename__ = 'Payments'
    TransactionID = db.Column(db.String(36), primary_key=True)
    OrderID = db.Column(db.String(36), db.ForeignKey('Orders.OrderID'), nullable=False)
    Amount = db.Column(db.Numeric(10,2), nullable=False)
    PaymentMethod = db.Column(db.Enum('Credit Card','Alipay','WeChat Pay'), 
                              default='Credit Card', nullable=False)
    Status = db.Column(db.Enum('Success','Failed','Pending'), 
                       default='Pending', nullable=False)

# ========== 3. 初始化数据库（如果表不存在则创建） ==========
with app.app_context():
    db.create_all()

# ========== 4. 工具函数：检查&扣减库存 ==========

def check_and_update_inventory(cart_items):
    """
    根据 Cart 中的商品，检查库存是否足够，并扣减库存。
    如果库存不足则返回 False。
    """
    for item in cart_items:
        product = Products.query.filter_by(ProductID=item.ProductID).first()
        if not product or product.InventoryCount < item.Quantity:
            return False
    # 扣库存
    for item in cart_items:
        product = Products.query.filter_by(ProductID=item.ProductID).first()
        product.InventoryCount -= item.Quantity
        db.session.add(product)
    db.session.commit()
    return True

def initiate_payment_gateway(total_amount):
    """
    调用或模拟第三方支付网关接口，返回一个支付交易ID (用于演示)。
    """
    return f"PAY-{uuid.uuid4().hex[:8]}"

# ========== 5. 核心：Checkout 路由 ==========

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    核心的“结账”流程示例：
    1. 获取 user_id、shipping_address、payment_method(可选)
    2. 查询 Cart 表得到所有购物车商品 & 计算总价
    3. 检查并扣库存
    4. 创建 Orders 记录，OrderID=UUID，状态=Processing
    5. 创建 Payments 记录，TransactionID=UUID，状态=Pending
    6. 回写 Orders.PaymentTransactionID
    7. 清空(或删除)购物车
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid request"}), 400

    user_id = data.get('UserID')
    shipping_address = data.get('ShippingAddress', '')
    payment_method = data.get('PaymentMethod', 'Credit Card')  # 默认“信用卡”
    
    # 简单校验
    if not user_id or not shipping_address:
        return jsonify({"message": "Missing user_id or shipping_address"}), 400
    
    # 1. 找到购物车里的所有条目
    cart_items = Cart.query.filter_by(UserID=user_id).all()
    if not cart_items:
        return jsonify({"message": "Cart is empty or user not found"}), 400

    # 2. 计算总价
    total_amount = 0
    for item in cart_items:
        product = Products.query.filter_by(ProductID=item.ProductID).first()
        total_amount += float(product.Price) * item.Quantity  # 转 float 便于加法

    if total_amount < 0.01:
        return jsonify({"message": "Total Amount is too small"}), 400

    # 3. 检查库存
    if not check_and_update_inventory(cart_items):
        return jsonify({"message": "Inventory not sufficient"}), 409

    # 4. 创建 Orders 表
    new_order_id = str(uuid.uuid4())  # CHAR(36)
    new_order = Orders(
        OrderID=new_order_id,
        UserID=user_id,
        TotalAmount=round(total_amount, 2),
        ShippingAddress=shipping_address,
        OrderStatus='Processing'     # 默认 Processing
    )
    db.session.add(new_order)
    db.session.commit()

    # 5. 模拟网关支付 -> 返回交易流水号
    payment_ref = initiate_payment_gateway(total_amount)

    # 6. 创建 Payments(状态=Pending)
    new_transaction_id = str(uuid.uuid4())  # TransactionID
    payment_record = Payments(
        TransactionID=new_transaction_id,
        OrderID=new_order_id,
        Amount=round(total_amount, 2),
        PaymentMethod=payment_method, 
        Status='Pending'
    )
    db.session.add(payment_record)
    db.session.commit()

    # 7. 回写 Orders 表中 PaymentTransactionID
    new_order.PaymentTransactionID = new_transaction_id
    db.session.add(new_order)
    db.session.commit()

    # 8. 清空该用户的购物车
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    # 返回订单信息
    return jsonify({
        "message": "Checkout initiated successfully",
        "OrderID": new_order_id,
        "PaymentTransactionID": new_transaction_id,
        "PaymentReference": payment_ref,
        "TotalAmount": str(total_amount)  # JSON 返回可转成字符串
    }), 200

# ========== 6. 可选：模拟支付回调，更新订单/支付状态 ==========

@app.route('/payment/callback', methods=['POST'])
def payment_callback():
    """
    假设第三方支付成功后，会POST到此回调。
    传入 { "OrderID": "...", "PaymentStatus": "Success" / "Failed" }
    """
    data = request.get_json()
    order_id = data.get('OrderID')
    payment_status = data.get('PaymentStatus', 'Failed')  # 默认失败

    order = Orders.query.filter_by(OrderID=order_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404

    payment = Payments.query.filter_by(OrderID=order_id).first()
    if not payment:
        return jsonify({"message": "Payment record not found"}), 404

    # 更新支付表
    if payment_status == 'Success':
        payment.Status = 'Success'
        db.session.add(payment)
        # 订单标记为已发货(或下一个状态)；或仅改成其他自定义状态
        order.OrderStatus = 'Shipped'
        db.session.add(order)
        db.session.commit()
        return jsonify({"message": "Payment success, order shipped"}), 200
    else:
        payment.Status = 'Failed'
        db.session.add(payment)
        order.OrderStatus = 'Cancelled'
        db.session.add(order)
        db.session.commit()
        return jsonify({"message": "Payment failed, order cancelled"}), 200

# ========== 7. 启动服务 ==========
if __name__ == '__main__':
    app.run(debug=True)
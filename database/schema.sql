
CREATE DATABASE IF NOT EXISTS buyzu;
USE buyzu;

-- 1. Category 表：用于商品分类
CREATE TABLE IF NOT EXISTS Category (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(50) NOT NULL UNIQUE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

-- 2. Users 表：存储用户账号信息
CREATE TABLE IF NOT EXISTS Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,         -- 4~50 个字符，数字/字母/下划线
    PasswordHash BINARY(60) NOT NULL,             -- bcrypt 加密，至少 8 位（大写/小写/数字）
    Email VARCHAR(255) NOT NULL                   -- 符合 RFC 5322，已验证
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

-- 3. Products 表：存储商品详情
CREATE TABLE IF NOT EXISTS Products (
    ProductID CHAR(12) PRIMARY KEY,               -- 主键，EAN-13 的简化格式
    ProductName VARCHAR(100) NOT NULL,
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL CHECK(Price >= 0.01),     -- >= 0.01
    CategoryID INT,
    InventoryCount INT NOT NULL DEFAULT 0 CHECK(InventoryCount >= 0), -- >=0，0表示无库存
    CONSTRAINT fk_product_category
        FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

-- 4. Cart 表：管理购物车条目
CREATE TABLE IF NOT EXISTS Cart (
    CartID INT AUTO_INCREMENT PRIMARY KEY,        -- 自增主键
    UserID INT NOT NULL,                          -- 外键，关联 Users
    ProductID CHAR(12) NOT NULL,                  -- 外键，关联 Products
    Quantity INT NOT NULL DEFAULT 1 CHECK(Quantity >= 1),  -- 数量>=1
    CONSTRAINT fk_cart_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_cart_product
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

-- 5. Orders 表：记录订单详情与状态
CREATE TABLE IF NOT EXISTS Orders (
    OrderID CHAR(36) PRIMARY KEY,                             -- 主键，UUID格式
    UserID INT NOT NULL,                                       -- 外键，关联 Users
    TotalAmount DECIMAL(10,2) NOT NULL CHECK(TotalAmount >= 0.01), -- 商品总价+运费
    ShippingAddress TEXT NOT NULL,                             -- 国家/邮编等格式已在应用层验证
    OrderStatus ENUM('Processing','Shipped','Delivered','Cancelled')
        NOT NULL DEFAULT 'Processing',                        -- 订单状态
    PaymentTransactionID VARCHAR(36) DEFAULT NULL,             -- 仅存交易ID，不设外键
    CONSTRAINT fk_order_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

-- 6. Payments 表：记录支付交易
CREATE TABLE IF NOT EXISTS Payments (
    TransactionID VARCHAR(36) PRIMARY KEY,  -- 主键，UUID格式
    OrderID CHAR(36) NOT NULL,             -- 外键，关联 Orders(OrderID)
    Amount DECIMAL(10,2) NOT NULL CHECK(Amount >= 0.01),  -- 与订单金额匹配
    PaymentMethod ENUM('Credit Card','Alipay','WeChat Pay') 
        NOT NULL DEFAULT 'Credit Card',    -- 支付方式
    Status ENUM('Success','Failed','Pending') 
        NOT NULL DEFAULT 'Pending',        -- 成功/失败/等待中
    CONSTRAINT fk_payment_order
        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

-- 7. Review 表：存储用户对商品的评价与评分
CREATE TABLE IF NOT EXISTS Reviews (
    ReviewID INT AUTO_INCREMENT PRIMARY KEY,  -- 自增主键
    UserID INT NOT NULL,                      -- 外键，关联 Users
    ProductID CHAR(12) NOT NULL,             -- 外键，关联 Products
    Rating INT NOT NULL CHECK(Rating BETWEEN 1 AND 5),  -- 评分 1~5
    Comment TEXT,                             -- 可选评论
    CONSTRAINT fk_review_user
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_review_product
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;
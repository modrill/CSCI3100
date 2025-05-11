DROP DATABASE IF EXISTS buyzu;
CREATE DATABASE IF NOT EXISTS buyzu;
USE buyzu;
CREATE TABLE orders (
    order_id          CHAR(36)      PRIMARY KEY,         
    user_id           BIGINT UNSIGNED NOT NULL,          
    total_amount      DECIMAL(10,2)  NOT NULL,           
    status            ENUM('pending', 'paid', 'failed', 'shipped', 'completed') DEFAULT 'pending',
    payment_method    ENUM('credit_card') DEFAULT 'credit_card',  
    shipping_method   VARCHAR(50)    NOT NULL,           
    phone             VARCHAR(20)    NOT NULL,          
    street_address    VARCHAR(255)   NOT NULL,           
    city              VARCHAR(50)    NOT NULL,           
    postal_code       VARCHAR(20)    NOT NULL,           
    country           ENUM('Hong Kong SAR', 'China', 'United States') NOT NULL
    created_at        DATETIME       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 订单商品项
CREATE TABLE order_items (
    order_item_id  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id       CHAR(36)      NOT NULL,
    productID     CHAR(12)      NOT NULL,              -- 关联商品表
    quantity       INT UNSIGNED  NOT NULL CHECK(quantity > 0),
    price          DECIMAL(10,2) NOT NULL CHECK(price >= 0.01), -- 下单时的价格快照

    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (productID) REFERENCES products(productID)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 支付记录
CREATE TABLE payments (
    payment_id      CHAR(36)      PRIMARY KEY,           
    order_id        CHAR(36)      NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,              
    status          ENUM('pending', 'succeeded', 'failed') DEFAULT 'pending',
    card_last4      CHAR(4)       NOT NULL,              
    transaction_id  VARCHAR(255)  NOT NULL,              

    FOREIGN KEY (order_id) REFERENCES orders(order_id)
) ENGINE=InnoDB CHARSET=utf8mb4;

-- 创建用户表
CREATE TABLE users (
    user_id         BIGINT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)      NOT NULL UNIQUE,
    password_hash   CHAR(60)         NOT NULL, 
    email           VARCHAR(255)     NOT NULL UNIQUE,
) ENGINE=InnoDB CHARSET=utf8mb4;
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS buyzu;

-- 使用buyzu数据库
USE buyzu;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'taotao'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON buyzu.* TO 'taotao'@'localhost';
FLUSH PRIVILEGES;

-- 创建验证码表（如果不存在）
CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    expiry_time DATETIME NOT NULL
);

-- 创建用户表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    google_id VARCHAR(255) DEFAULT NULL UNIQUE
);

-- 可选：创建一个测试管理员账户
-- 注：密码字段需要使用Hash值，这里只是占位，实际使用时需替换
-- INSERT INTO users (username, password, email) VALUES 
-- ('admin', 'pbkdf2:sha256:260000$HASH_HERE', 'admin@example.com'); 
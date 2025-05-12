-- 使用buyzu数据库
USE buyzu;

-- 检查是否需要添加is_admin列
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'buyzu' 
AND TABLE_NAME = 'users' 
AND COLUMN_NAME = 'is_admin';

-- 如果is_admin列不存在，添加列
SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT "is_admin column already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查是否需要添加created_at列
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'buyzu' 
AND TABLE_NAME = 'users' 
AND COLUMN_NAME = 'created_at';

-- 如果created_at列不存在，添加列
SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
    'SELECT "created_at column already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查是否有管理员账户，如果没有则创建默认管理员
SET @admin_exists = 0;
SELECT COUNT(*) INTO @admin_exists FROM users WHERE username = 'admin';

SET @sql = IF(@admin_exists = 0, 
    'INSERT INTO users (username, password, email, is_admin) VALUES ("admin", "pbkdf2:sha256:260000$Kv2CWA9t$a8d3b67da85f508e1b9fe1d8fcc9267c2775ce30e9a2b954aea02f1b57aa7ad8", "admin@example.com", 1)',
    'UPDATE users SET is_admin = 1 WHERE username = "admin"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 显示用户表的当前结构
DESCRIBE users; 
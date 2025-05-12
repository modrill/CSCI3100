-- Use buyzu database
USE buyzu;

-- Check if is_admin column needs to be added
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'buyzu' 
AND TABLE_NAME = 'users' 
AND COLUMN_NAME = 'is_admin';

-- If is_admin column doesn't exist, add it
SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT "is_admin column already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if created_at column needs to be added
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'buyzu' 
AND TABLE_NAME = 'users' 
AND COLUMN_NAME = 'created_at';

-- If created_at column doesn't exist, add it
SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
    'SELECT "created_at column already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if admin account exists, create default admin if not
SET @admin_exists = 0;
SELECT COUNT(*) INTO @admin_exists FROM users WHERE username = 'admin';

SET @sql = IF(@admin_exists = 0, 
    'INSERT INTO users (username, password, email, is_admin) VALUES ("admin", "pbkdf2:sha256:260000$Kv2CWA9t$a8d3b67da85f508e1b9fe1d8fcc9267c2775ce30e9a2b954aea02f1b57aa7ad8", "admin@example.com", 1)',
    'UPDATE users SET is_admin = 1 WHERE username = "admin"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Show current users table structure
DESCRIBE users; 
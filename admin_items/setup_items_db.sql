-- Use buyzu database
USE buyzu;

-- Check if products table exists, if not create it
CREATE TABLE IF NOT EXISTS products (
    productID         CHAR(12)     PRIMARY KEY,
    productName       VARCHAR(100) NOT NULL,
    descri            TEXT,
    price             DECIMAL(10,2) NOT NULL CHECK(price >= 0.01),
    categoryID        INT,
    brandID           INT,
    img               VARCHAR(255) NOT NULL,
    currentStatus     TINYINT      NOT NULL DEFAULT 0,
    inventoryCount    INT          NOT NULL DEFAULT 0 CHECK(inventoryCount >= 0),
    rating            FLOAT        NOT NULL DEFAULT 0,
    sales             INT          NOT NULL DEFAULT 0
);

-- Check if category table exists, if not create it
CREATE TABLE IF NOT EXISTS category (
    categoryID        INT          AUTO_INCREMENT PRIMARY KEY,
    categoryName      VARCHAR(100) NOT NULL,
    categoryDesc      TEXT
);

-- Check if brand table exists, if not create it
CREATE TABLE IF NOT EXISTS brand (
    brandID           INT          AUTO_INCREMENT PRIMARY KEY,
    brandName         VARCHAR(100) NOT NULL,
    brandDesc         TEXT
);

-- Add foreign key constraints if not already present
-- This will only work if the tables already have data
-- For a new installation, these should be included in the table creation statements above
SET @fk1_exists = (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = 'buyzu'
    AND TABLE_NAME = 'products'
    AND CONSTRAINT_NAME = 'fk_prod_cat'
);

SET @fk2_exists = (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = 'buyzu'
    AND TABLE_NAME = 'products'
    AND CONSTRAINT_NAME = 'fk_prod_brand'
);

SET @sql1 = IF(@fk1_exists = 0, 
    'ALTER TABLE products ADD CONSTRAINT fk_prod_cat FOREIGN KEY (categoryID) REFERENCES category(categoryID) ON DELETE SET NULL ON UPDATE CASCADE',
    'SELECT "Category foreign key already exists"');

SET @sql2 = IF(@fk2_exists = 0, 
    'ALTER TABLE products ADD CONSTRAINT fk_prod_brand FOREIGN KEY (brandID) REFERENCES brand(brandID) ON DELETE SET NULL ON UPDATE CASCADE',
    'SELECT "Brand foreign key already exists"');

PREPARE stmt1 FROM @sql1;
EXECUTE stmt1;
DEALLOCATE PREPARE stmt1;

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- Insert some sample categories if none exist
INSERT IGNORE INTO category (categoryID, categoryName, categoryDesc) VALUES
(1, 'Electronics', 'Electronic devices and accessories'),
(2, 'Clothing', 'Apparel and fashion items'),
(3, 'Home & Kitchen', 'Home goods and kitchen appliances'),
(4, 'Books', 'Books, e-books, and publications'),
(5, 'Toys & Games', 'Toys, games, and entertainment items');

-- Insert some sample brands if none exist
INSERT IGNORE INTO brand (brandID, brandName, brandDesc) VALUES
(1, 'Apple', 'Consumer electronics and software'),
(2, 'Samsung', 'Electronics and appliances'),
(3, 'Nike', 'Athletic apparel and footwear'),
(4, 'Amazon Basics', 'Amazon\'s private label products'),
(5, 'Sony', 'Electronics, entertainment, and gaming');

-- Insert some sample products if none exist
INSERT IGNORE INTO products (productID, productName, descri, price, categoryID, brandID, img, currentStatus, inventoryCount, rating, sales) VALUES
('P000000000001', 'iPhone 13', 'Apple iPhone 13 with 128GB storage', 799.99, 1, 1, '/images/products/iphone13.jpg', 1, 50, 4.8, 1200),
('P000000000002', 'Samsung Galaxy S21', 'Samsung Galaxy S21 with 128GB storage', 699.99, 1, 2, '/images/products/galaxys21.jpg', 1, 35, 4.7, 950),
('P000000000003', 'Nike Air Max', 'Nike Air Max running shoes', 129.99, 2, 3, '/images/products/nikeairmax.jpg', 1, 100, 4.5, 500),
('P000000000004', 'Amazon Echo Dot', 'Smart speaker with Alexa', 49.99, 1, 4, '/images/products/echodot.jpg', 1, 200, 4.6, 2500),
('P000000000005', 'Sony PlayStation 5', 'Next-gen gaming console', 499.99, 1, 5, '/images/products/ps5.jpg', 1, 10, 4.9, 750);

-- Show products table structure
DESCRIBE products;

-- Show sample data
SELECT p.productID, p.productName, p.price, c.categoryName, b.brandName
FROM products p
LEFT JOIN category c ON p.categoryID = c.categoryID
LEFT JOIN brand b ON p.brandID = b.brandID
LIMIT 10; 
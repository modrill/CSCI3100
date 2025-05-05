# CSCI3100

v1.0.0 

src里面存放了front-end/back-end
dataset&database相关可以放在database文件夹里，包括前端素材也可以放进去（或者开个temp文件夹）
某部分的代码可以开个temp文件放着慢慢调试

前端可以先写个框架（黑白框框加文字），后面统一样式再细改
目前我这边用的是php/html+js

米娜桑加油捏(ง •_•)ง

v1.1.0

我在database文件夹里放了一个包含商品分类，品牌和具体描述外加图片的测试数据库
图片路径是images/products/$px$.jpeg，$px$对应的是productId，例如productId为33的商品对应的图片是p33.jpeg
继承使用apache+mysql+php，算法部分我准备用python编写
大家还有需要的信息我可以再加进去，比如其他的商品类别和商品信息

期末周加油捏(｀･ω･´)ゞ

v1.1.1

改进了一下buyzu_item.sql，字段名和schema.sql里面的保持一致了，然后下面是暂定的变量定义：

Category（schema.sql & buyzu_item.sql）

CategoryID INT PRIMARY KEY
CategoryName VARCHAR(50) NOT NULL
Brand（buyzu_item.sql 中新增）

BrandID INT PRIMARY KEY
BrandName VARCHAR(50) NOT NULL
Users（schema.sql）

UserID INT AUTO_INCREMENT PRIMARY KEY
Username VARCHAR(50) NOT NULL UNIQUE
PasswordHash BINARY(60) NOT NULL
Email VARCHAR(255) NOT NULL
Products（schema.sql & buyzu_item.sql）

ProductID CHAR(12) PRIMARY KEY
ProductName VARCHAR(100) NOT NULL
Description TEXT
Price DECIMAL(10,2) NOT NULL CHECK(Price >= 0.01)
CategoryID INT
· FK → Category(CategoryID) ON DELETE SET NULL ON UPDATE CASCADE
BrandID INT
· FK → Brand(BrandID) ON DELETE SET NULL ON UPDATE CASCADE
Image VARCHAR(255) NOT NULL
Type TINYINT NOT NULL DEFAULT 0
InventoryCount INT NOT NULL DEFAULT 0 CHECK(InventoryCount >= 0)
Rate FLOAT NOT NULL
Sales INT NOT NULL
Cart（schema.sql）

CartID INT AUTO_INCREMENT PRIMARY KEY
UserID INT NOT NULL
· FK → Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
ProductID CHAR(12) NOT NULL
· FK → Products(ProductID) ON DELETE CASCADE ON UPDATE CASCADE
Quantity INT NOT NULL DEFAULT 1 CHECK(Quantity >= 1)
Orders（schema.sql）

OrderID CHAR(36) PRIMARY KEY
UserID INT NOT NULL
· FK → Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
TotalAmount DECIMAL(10,2) NOT NULL CHECK(TotalAmount >= 0.01)
ShippingAddress TEXT NOT NULL
OrderStatus ENUM('Processing','Shipped','Delivered','Cancelled') NOT NULL DEFAULT 'Processing'
PaymentTransactionID VARCHAR(36) DEFAULT NULL
Payments（schema.sql）

TransactionID VARCHAR(36) PRIMARY KEY
OrderID CHAR(36) NOT NULL
· FK → Orders(OrderID) ON DELETE CASCADE ON UPDATE CASCADE
Amount DECIMAL(10,2) NOT NULL CHECK(Amount >= 0.01)
PaymentMethod ENUM('Credit Card','Alipay','WeChat Pay') NOT NULL DEFAULT 'Credit Card'
Status ENUM('Success','Failed','Pending') NOT NULL DEFAULT 'Pending'
Reviews（schema.sql）

ReviewID INT AUTO_INCREMENT PRIMARY KEY
UserID INT NOT NULL
· FK → Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
ProductID CHAR(12) NOT NULL
· FK → Products(ProductID) ON DELETE CASCADE ON UPDATE CASCADE
Rating INT NOT NULL CHECK(Rating BETWEEN 1 AND 5)
Comment TEXT

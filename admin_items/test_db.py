#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import mysql.connector
from pprint import pprint
import getpass

def test_connection():
    """测试数据库连接"""
    # 提示用户输入密码
    password = getpass.getpass("请输入MySQL密码: ")
    
    # 设置数据库连接参数
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': password,
        'database': 'buyzu'
    }
    
    try:
        conn = mysql.connector.connect(**db_config)
        print("数据库连接成功!")
        
        # 使用字典游标
        cursor = conn.cursor(dictionary=True)
        
        # 1. 测试products表基本查询
        cursor.execute("SELECT COUNT(*) as count FROM products")
        count = cursor.fetchone()
        print(f"Products表中共有 {count['count']} 条记录")
        
        # 2. 查看前5条产品记录
        cursor.execute("SELECT productID, productName, categoryID, brandID, price FROM products LIMIT 5")
        products = cursor.fetchall()
        print("\n前5条产品记录:")
        pprint(products)
        
        # 3. 测试category表
        cursor.execute("SELECT * FROM category")
        categories = cursor.fetchall()
        print(f"\n类别表中共有 {len(categories)} 条记录:")
        pprint(categories)
        
        # 4. 测试brand表
        cursor.execute("SELECT * FROM brand")
        brands = cursor.fetchall()
        print(f"\n品牌表中共有 {len(brands)} 条记录")
        
        # 5. 测试连表查询
        cursor.execute("""
            SELECT p.productID, p.productName, c.categoryName, b.brandName, p.price
            FROM products p
            LEFT JOIN category c ON p.categoryID = c.categoryID
            LEFT JOIN brand b ON p.brandID = b.brandID
            LIMIT 5
        """)
        joined_data = cursor.fetchall()
        print("\n连表查询结果:")
        pprint(joined_data)
        
        cursor.close()
        conn.close()
        print("\n数据库测试完成!")
        
        # 返回密码供其他脚本使用
        return password
    except Exception as e:
        print(f"错误: {e}")
        return None

if __name__ == "__main__":
    test_connection() 
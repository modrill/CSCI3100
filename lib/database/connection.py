import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager

# 数据库配置，可通过环境变量覆盖
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'taotao'),
    'password': os.environ.get('DB_PASSWORD', '123456'),
    'database': os.environ.get('DB_NAME', 'buyzu'),
    'charset': 'utf8mb4'
}

class DBConnectionPool:
    """数据库连接池类，单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnectionPool, cls).__new__(cls)
            cls._instance._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="buyzu_pool",
                pool_size=5,
                **DB_CONFIG
            )
        return cls._instance
    
    def get_connection(self):
        """获取数据库连接"""
        return self._pool.get_connection()


@contextmanager
def get_connection():
    """
    上下文管理器，自动处理连接的获取和关闭
    
    用法:
    with get_connection() as (conn, cursor):
        cursor.execute("SELECT * FROM products")
        results = cursor.fetchall()
    """
    conn = None
    cursor = None
    try:
        conn = DBConnectionPool().get_connection()
        cursor = conn.cursor(dictionary=True)
        yield conn, cursor
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
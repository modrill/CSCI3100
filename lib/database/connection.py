import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager
import time

# 数据库配置，可通过环境变量覆盖
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'taotao'),
    'password': os.environ.get('DB_PASSWORD', '123456'),
    'database': os.environ.get('DB_NAME', 'buyzu'),
    'charset': 'utf8mb4',
    'use_pure': True,
    'pool_name': 'buyzu_pool',
    'pool_size': 10,
    'get_warnings': True,
    'autocommit': True
}

class DBConnectionPool:
    """数据库连接池类，单例模式"""
    
    _instance = None
    _pool = None
    _max_retries = 3  # 最大重试次数
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnectionPool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._create_pool()
    
    def _create_pool(self):
        """创建连接池，带重试机制"""
        retry_count = 0
        last_error = None
        
        while retry_count < self._max_retries:
            try:
                self._pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)
                print("数据库连接池创建成功")
                return
            except Exception as e:
                last_error = e
                retry_count += 1
                print(f"创建连接池失败，第{retry_count}次重试: {str(e)}")
                if retry_count < self._max_retries:
                    time.sleep(1)  # 等待1秒后重试
        
        print(f"连接池创建失败，已达到最大重试次数: {str(last_error)}")
        raise last_error
    
    def get_connection(self):
        """获取数据库连接，带重试机制"""
        if self._pool is None:
            self._create_pool()
        
        retry_count = 0
        last_error = None
        
        while retry_count < self._max_retries:
            try:
                conn = self._pool.get_connection()
                return conn
            except Exception as e:
                last_error = e
                retry_count += 1
                print(f"获取连接失败，第{retry_count}次重试: {str(e)}")
                if retry_count < self._max_retries:
                    time.sleep(1)  # 等待1秒后重试
                    # 如果连接池可能已满，尝试重新创建
                    if "pool exhausted" in str(e).lower():
                        print("连接池已满，尝试重新创建连接池")
                        self._pool = None
                        self._create_pool()
        
        print(f"获取连接失败，已达到最大重试次数: {str(last_error)}")
        raise last_error

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
        pool = DBConnectionPool()
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        yield conn, cursor
    except Exception as e:
        print(f"数据库操作异常: {str(e)}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"关闭cursor失败: {str(e)}")
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"关闭连接失败: {str(e)}")
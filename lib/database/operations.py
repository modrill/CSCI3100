from .connection import get_connection
from .exception import DatabaseError

def execute_query(query, params=None, fetch_one=False):
    """
    执行查询操作并返回结果
    
    参数:
        query (str): SQL查询语句
        params (tuple|dict): 查询参数
        fetch_one (bool): 是否只获取一条记录
        
    返回:
        list|dict: 查询结果
    """
    try:
        with get_connection() as (conn, cursor):
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    except Exception as e:
        raise DatabaseError(f"查询执行失败: {str(e)}")

def execute_update(query, params=None):
    """
    执行更新操作并返回影响的行数
    
    参数:
        query (str): SQL更新语句
        params (tuple|dict): 更新参数
        
    返回:
        int: 受影响的行数
    """
    try:
        with get_connection() as (conn, cursor):
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        raise DatabaseError(f"更新执行失败: {str(e)}")

def execute_batch(query, params_list):
    """
    批量执行SQL操作
    
    参数:
        query (str): SQL语句
        params_list (list): 参数列表，每个元素对应一次执行
        
    返回:
        int: 受影响的行数
    """
    if not params_list:
        return 0
        
    try:
        with get_connection() as (conn, cursor):
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        raise DatabaseError(f"批量操作失败: {str(e)}")

def execute_transaction(operations):
    """
    在一个事务中执行多个操作
    
    参数:
        operations (list): 操作列表，每个操作是一个(query, params)元组
        
    返回:
        bool: 事务是否成功
    """
    if not operations:
        return True
        
    try:
        with get_connection() as (conn, cursor):
            for query, params in operations:
                cursor.execute(query, params or ())
            conn.commit()
            return True
    except Exception as e:
        raise DatabaseError(f"事务执行失败: {str(e)}")
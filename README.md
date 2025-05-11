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

*改进了一下buyzu_item.sql，字段名和schema.sql里面的保持一致了，然后下面是暂定的变量定义：*
**已废除**

v1.1.2

数据库字段名用了更规范的驼峰命名法，详情参见database/buyzu_item.sql里面的具体定义

v1.1.3
关于lib-database中方法说明
connection.py: 数据库连接
exception.py:异常？
operations.py：数据库操作。

具体使用方法：
Connection:
    DB_CONFIG:: 定义数据库连接所需的基本配置（主机、用户、密码、数据库名、字符集）
    DBConnectionPool:实现数据库连接池，采用单例模式，确保整个应用共享同一个连接池实例。
    提供 get_connection() -》从连接池中获取一个数据库连接
    get_connection用法
        with get_connection() as (conn, cursor):
        cursor.execute("SELECT * FROM products")
        results = cursor.fetchall()

Exception:
    针对operation中的错误：
    例子
    try:
        users = execute_query("SELECT * FROM users")
    except DatabaseError as e:
        print(f"捕获到数据库错误: {e}")

    ->一般其实就用到这两个捏
Operations：
    execute_query(query, params=None, fetch_one=False) ->查询
    输入: SQL查询语句 (query)，可选的查询参数 (params)，可选的是否只取一条记录的布尔值 (fetch_one)。
    输出: 如果 fetch_one 为 True，返回单条查询结果 (字典) 或 None；否则返回多条查询结果 (字典列表)。
    例子：
    user = execute_query("SELECT id, name FROM users WHERE id = %s", params=(1,), fetch_one=True)
    if user:
        print(f"单个用户: {user}")
    然后execute_query(q)

    execute_update(query, params=None)->执行insert，delete，update等
    输入：SQL更新、插入或删除语句 (query)，可选的参数 (params)
    输出: 操作影响的数据库行数。 凑数的，无视就好

    rows_affected = execute_update(
        "UPDATE users SET email = %s WHERE name = %s",
        params=("updated@example.com", "新用户")
    ) -》更新用户邮箱

    execute_batch(query, params_list) ->批量执行同一条SQL语句多次（
    输入：SQL语句模板 (query)，参数列表 (params_list)，其中每个元素是对应一次执行的参数。
    输出: 操作影响的总数据库行数。凑数的，无视就好
eg:
    users_to_insert = [
        ("用户A", "a@example.com"),
        ("用户B", "b@example.com"),
        ("用户C", "c@example.com")
    ]
    rows_affected = execute_batch(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        users_to_insert
    )

  
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.database import execute_query, execute_update, execute_batch
from lib.database.exception import DatabaseError

def test_connection():
    """测试数据库连接"""
    try:
        # 执行简单查询
        result = execute_query("SELECT 1 as test")
        print("连接测试成功:", result)
        return True
    except DatabaseError as e:
        print(f"连接测试失败: {e}")
        return False

def test_query():
    """测试查询操作"""
    try:
        # 查询所有类别
        categories = execute_query("SELECT * FROM category")
        print(f"查询成功，共找到 {len(categories)} 个类别:")
        for category in categories:
            print(f"  - ID: {category['categoryID']}, 名称: {category['categoryName']}")
        return True
    except DatabaseError as e:
        print(f"查询测试失败: {e}")
        return False



def run_tests():
    """运行所有测试"""
    tests = [
        ("连接测试", test_connection),
        ("查询测试", test_query),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n开始 {name}...")
        success = test_func()
        results.append((name, success))
        print(f"{name} {'成功' if success else '失败'}")
    
    print("\n测试结果汇总:")
    all_success = True
    for name, success in results:
        print(f"  - {name}: {'✓' if success else '✗'}")
        if not success:
            all_success = False
    
    print(f"\n总体结果: {'所有测试通过' if all_success else '有测试失败'}")
    return all_success

if __name__ == "__main__":
    run_tests()
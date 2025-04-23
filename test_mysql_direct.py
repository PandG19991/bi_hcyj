import pymysql
import sys
import traceback

# 重定向输出到文件
with open('mysql_test_result.txt', 'w', encoding='utf-8') as f:
    try:
        f.write("开始测试数据库连接...\n")
        
        # 连接参数
        host = 'localhost'
        user = 'testuser'
        password = 'TestPassword123!'
        database = 'xiaoe_sync'
        
        f.write(f"尝试连接到 MySQL: {user}@{host}/{database}\n")
        
        # 尝试连接
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        # 执行简单查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            f.write(f"查询结果: {result}\n")
            
        conn.close()
        f.write("连接成功并已关闭!\n")
        
    except Exception as e:
        f.write(f"连接失败! 错误类型: {type(e).__name__}\n")
        f.write(f"错误信息: {str(e)}\n")
        f.write("详细错误堆栈:\n")
        traceback.print_exc(file=f)
        
print("测试完成，请查看 mysql_test_result.txt 文件获取结果") 
import pymysql
import traceback
import sys # 引入 sys 模块

print("开始测试 bi 用户连接...")

try:
    # 使用bi用户连接
    print("尝试连接 (bi@127.0.0.1)...")
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306, # 显式指定端口
        user='bi',
        password='SRTMyktZSL36rbzY',
        db='xiaoe_sync',
        charset='utf8mb4',
        connect_timeout=10 # 添加连接超时设置
    )
    print("连接对象创建成功。") # 添加连接成功后的打印

    # 执行测试查询
    print("尝试执行查询...")
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"查询结果: {result}")

    conn.close()
    print("bi用户连接成功!")

except pymysql.Error as e: # 捕获更具体的 PyMySQL 错误
    print(f"PyMySQL 连接或操作失败! 错误代码: {e.args[0]}, 错误信息: {e.args[1]}", file=sys.stderr)
    traceback.print_exc() # 打印完整的错误堆栈
except Exception as e:
    print(f"发生未知错误! 错误类型: {type(e).__name__}, 错误信息: {str(e)}", file=sys.stderr)
    traceback.print_exc() # 打印完整的错误堆栈
finally:
    print("测试结束。") # 确保总是打印结束信息 
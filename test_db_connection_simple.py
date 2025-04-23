import pymysql

def test_simple_connection():
    print("开始测试数据库连接...")
    
    # 从配置文件的 DATABASE_URL 中提取的信息
    host = 'localhost'
    user = 'testuser'
    password = 'TestPassword123!'
    database = 'xiaoe_sync'
    
    try:
        # 尝试直接连接
        print(f"尝试连接到 MySQL: {user}@{host}/{database}")
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
            print(f"查询结果: {result}")
            
        conn.close()
        print("连接成功并已关闭!")
        
    except Exception as e:
        print(f"连接失败! 错误: {type(e).__name__}: {str(e)}")
        
if __name__ == "__main__":
    test_simple_connection() 
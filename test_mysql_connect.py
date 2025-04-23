import pymysql
import os
import traceback

def test_testuser_connection():
    """测试新创建的testuser用户连接"""
    print("-" * 50)
    print("测试 testuser 用户连接:")
    print("-" * 50)
    
    try:
        # 使用新创建的testuser用户连接
        print("尝试连接 (testuser@127.0.0.1)...")
        conn = pymysql.connect(
            host='127.0.0.1',
            user='testuser',
            password='TestPassword123!', 
            db='xiaoe_sync',
            charset='utf8mb4'
        )
        
        # 执行测试查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"查询结果: {result}")
        
        conn.close()
        print("testuser用户连接成功!")
        return True
        
    except Exception as e:
        print(f"testuser用户连接失败! 错误: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

def test_bi_connection():
    """测试原始bi用户连接"""
    print("\n" + "-" * 50)
    print("测试 bi 用户连接:")
    print("-" * 50)
    
    try:
        # 使用原始bi用户连接
        print("尝试连接 (bi@127.0.0.1)...")
        conn = pymysql.connect(
            host='127.0.0.1',
            user='bi',
            password='SRTMyktZSL36rbzY',
            db='xiaoe_sync', 
            charset='utf8mb4'
        )
        
        # 执行测试查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"查询结果: {result}")
        
        conn.close()
        print("bi用户连接成功!")
        return True
        
    except Exception as e:
        print(f"bi用户连接失败! 错误: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

def check_mysql_users():
    """尝试通过root连接查询用户表"""
    print("\n" + "-" * 50)
    print("检查 MySQL 用户表 (需要root权限):")
    print("-" * 50)
    
    try:
        # 这里需要用户输入root密码
        root_password = input("请输入MySQL root密码以检查用户表 (如不想检查请直接按回车): ")
        if not root_password:
            print("跳过用户表检查。")
            return
            
        # 连接数据库
        print("尝试使用root连接...")
        conn = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password=root_password,
            charset='utf8mb4'
        )
        
        # 查询用户表
        with conn.cursor() as cursor:
            print("\n用户及主机列表:")
            cursor.execute("SELECT User, Host, plugin FROM mysql.user WHERE User IN ('bi', 'testuser')")
            users = cursor.fetchall()
            if users:
                for user in users:
                    print(f"用户: {user[0]}, 主机: {user[1]}, 认证插件: {user[2]}")
                    
                    # 查看权限
                    try:
                        cursor.execute(f"SHOW GRANTS FOR '{user[0]}'@'{user[1]}'")
                        grants = cursor.fetchall()
                        print(f"  权限:")
                        for grant in grants:
                            print(f"    {grant[0]}")
                    except Exception as e:
                        print(f"  无法获取权限信息: {str(e)}")
            else:
                print("未找到 'bi' 或 'testuser' 用户!")
                
        conn.close()
        print("\n用户检查完成!")
        
    except Exception as e:
        print(f"检查用户表失败! 错误: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    print("MySQL 连接测试开始...")
    
    # 测试两个用户连接
    testuser_ok = test_testuser_connection()
    bi_ok = test_bi_connection()
    
    # 如果两个用户都连接失败，尝试检查用户表
    if not testuser_ok and not bi_ok:
        check_mysql_users()
    
    print("\nMySQL 连接测试结束。") 
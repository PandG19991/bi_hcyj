import sys
import os

# 确保能导入 config 和 core
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from config.config import settings # 导入配置

def test_connection():
    db_url = settings.DATABASE_URL
    print(f"Attempting to connect using DATABASE_URL: {db_url}")

    if not db_url:
        print("Error: DATABASE_URL is not set in your config/.env file.")
        return

    try:
        # 创建引擎
        engine = create_engine(db_url)

        # 尝试连接
        print("Attempting engine.connect()...")
        with engine.connect() as connection:
            print("Connection successful!")
            # 可以尝试执行一个简单的查询
            # result = connection.execute(text("SELECT 1"))
            # print("Executed SELECT 1, result:", result.scalar_one())
            print("Database connection test passed.")

    except OperationalError as e:
        print("\n-------------------------------------")
        print("!!! DATABASE CONNECTION FAILED !!!")
        print("-------------------------------------")
        print(f"Error Type: {type(e)}")
        print(f"Error Details: {e}")
        print("\nPlease double-check:")
        print("1. MySQL server is running.")
        print("2. Hostname/IP in DATABASE_URL is correct and reachable.")
        print("3. Port in DATABASE_URL is correct (default 3306).")
        print("4. Database name in DATABASE_URL exists on the server.")
        print(f"5. User ('{engine.url.username}') exists and has the correct password.")
        print(f"6. User ('{engine.url.username}') is granted permission to connect from your current location ('{engine.url.host}' or implicitly 'localhost'). Check MySQL grants.")
        print(f"7. User ('{engine.url.username}') authentication plugin is compatible (try mysql_native_password).")

    except Exception as e:
        print("\n-------------------------------------")
        print("!!! AN UNEXPECTED ERROR OCCURRED !!!")
        print("-------------------------------------")
        print(f"Error Type: {type(e)}")
        print(f"Error Details: {e}")

if __name__ == "__main__":
    test_connection() 
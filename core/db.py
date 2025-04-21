from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from config.config import settings
from utils.logger import logger # 导入 logger

logger.info(f"Initializing database connection to: {settings.DATABASE_URL[:15]}...")

try:
    # 创建数据库引擎
    # echo=False: 不打印 SQL 语句到控制台 (生产环境建议 False)
    # pool_recycle=3600: 回收空闲超过 1 小时的连接，避免 MySQL "gone away" 错误
    # pool_pre_ping=True: 在每次从连接池获取连接前进行 ping 测试，确保连接有效
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_recycle=3600,
        pool_pre_ping=True
    )

    # 创建数据库会话工厂
    # autocommit=False: 事务需要手动提交
    # autoflush=False: 不自动 flush，提高性能，但在查询前可能需要手动 flush
    # bind=engine: 将会话工厂绑定到数据库引擎
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    # 使用 scoped_session 确保线程安全
    # 它为每个线程提供一个独立的 Session 实例
    db_session = scoped_session(SessionLocal)

    # 创建所有 SQLAlchemy 模型的基础类
    # 所有的数据模型类都需要继承自这个 Base
    Base = declarative_base()
    Base.query = db_session.query_property() # 可选：为模型添加 .query 属性

    logger.info("Database engine and session configured successfully.")

except Exception as e:
    logger.critical(f"Failed to initialize database connection: {e}", exc_info=True)
    # 在无法连接数据库时，可能需要退出程序或进行其他处理
    raise # 重新抛出异常，让上层知道初始化失败

def get_db():
    """依赖注入函数，用于获取数据库会话。"""
    db = db_session()
    try:
        yield db
    finally:
        # 在请求结束后关闭会话，将连接放回连接池
        db_session.remove()

# 可以在这里添加一个简单的连接测试函数 (可选)
def test_db_connection():
    """测试数据库连接是否正常。"""
    try:
        # 尝试获取一个会话并执行一个简单的查询
        db = next(get_db())
        db.execute("SELECT 1")
        logger.info("Database connection test successful.")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}", exc_info=True)
        return False
    finally:
        # 确保测试后也会关闭会话
        db_session.remove()

# 如果直接运行此文件，可以执行连接测试
# if __name__ == "__main__":
#     test_db_connection() 
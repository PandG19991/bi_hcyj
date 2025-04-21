import os
from dotenv import load_dotenv

# 获取项目根目录 (假设 config.py 在 config/ 目录下, 项目根目录是其上两级)
# 如果结构不同，需要调整这里的路径计算
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env 文件路径
dotenv_path = os.path.join(BASE_DIR, 'config', '.env')

# 仅当 .env 文件存在时加载
if os.path.exists(dotenv_path):
    # print(f"Loading .env file from: {dotenv_path}") # 移除 print，依赖日志
    load_dotenv(dotenv_path=dotenv_path, verbose=True)
# else:
    # print(f".env file not found at: {dotenv_path}") # 移除 print

class Settings:
    """应用程序配置类，从环境变量加载配置。"""
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./default.db') # 提供默认值以防 .env 缺失
    XIAOE_APP_ID: str = os.getenv('XIAOE_APP_ID')
    XIAOE_CLIENT_ID: str = os.getenv('XIAOE_CLIENT_ID')
    XIAOE_SECRET_KEY: str = os.getenv('XIAOE_SECRET_KEY')

    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    # 添加日志文件路径配置
    LOG_DIR: str = os.path.join(BASE_DIR, 'logs') # 日志目录
    LOG_FILE_APP: str = os.path.join(LOG_DIR, 'app.log') # 主应用日志
    LOG_FILE_CRON_INC: str = os.path.join(LOG_DIR, 'cron_incremental.log') # 增量任务日志
    LOG_FILE_CRON_STATUS: str = os.path.join(LOG_DIR, 'cron_status_update.log') # 状态更新任务日志

    ORDERS_SYNC_INTERVAL_MINUTES: int = int(os.getenv('ORDERS_SYNC_INTERVAL_MINUTES', 30))
    STATUS_UPDATE_INTERVAL_HOURS: int = int(os.getenv('STATUS_UPDATE_INTERVAL_HOURS', 1))
    STATUS_UPDATE_DAYS: int = int(os.getenv('STATUS_UPDATE_DAYS', 15))
    API_RETRY_TIMES: int = int(os.getenv('API_RETRY_TIMES', 3))
    API_RETRY_DELAY_SECONDS: int = int(os.getenv('API_RETRY_DELAY_SECONDS', 5))

    # 可以在这里添加其他需要的配置项转换或校验

    # 移除 __post_init__ 中的 makedirs，因为 logger 初始化时会创建
    # def __post_init__(self):
    #     # 确保日志目录存在
    #     os.makedirs(self.LOG_DIR, exist_ok=True)

# 创建配置实例供其他模块导入
settings = Settings()

# 移除原来在这里的 print 语句
# print(f"Database URL (masked): {settings.DATABASE_URL[:15]}...")
# print(f"Log Level: {settings.LOG_LEVEL}")
# print(f"Log Dir: {settings.LOG_DIR}") 
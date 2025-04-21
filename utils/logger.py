import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# 只获取 logger 实例，配置将在 setup_logging 中完成
logger = logging.getLogger()

# 日志格式可以先定义好
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logging():
    """配置日志记录器。"""
    # 在函数内部导入 settings，避免循环导入
    from config.config import settings

    # 清理已存在的 handlers，防止重复添加 (尤其是在交互式环境或多次调用时)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 设置日志级别
    logger.setLevel(settings.LOG_LEVEL)

    # --- 控制台 Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # --- 文件 Handler (Rotating) ---
    # 确保日志目录存在
    try:
        os.makedirs(settings.LOG_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.LOG_FILE_APP,
            maxBytes=5*1024*1024, # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
        log_file_path = settings.LOG_FILE_APP
    except Exception as e:
        logger.error(f"Failed to create or add file handler for {settings.LOG_FILE_APP}: {e}", exc_info=True)
        log_file_path = "None"


    # --- 针对特定库调整日志级别 (可选) ---
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)

    logger.info(f"Logger initialized with level: {settings.LOG_LEVEL}. Logging to console and file: {log_file_path}")

# 移除原来在顶层的日志配置代码和 logger.info 调用 
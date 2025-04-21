# 配置说明

项目配置通过根目录下的 `.env` 文件进行管理，使用 `python-dotenv` 库加载。

## 配置文件 (`.env`)

在项目根目录下的 `config/` 目录中创建一个名为 `.env` 的文件。**请确保将 `config/.env` 文件添加到 `.gitignore` 中，避免将敏感信息提交到版本库！**

`.env` 文件内容示例：

```dotenv
# 数据库配置 (使用 SQLAlchemy 连接字符串格式)
# 例如 MySQL: mysql+pymysql://user:password@host:port/database?charset=utf8mb4
DATABASE_URL=mysql+pymysql://your_db_user:your_db_password@127.0.0.1:3306/your_database_name?charset=utf8mb4

# 小鹅通 API 配置
XIAOE_APP_ID=your_xiaoe_app_id
XIAOE_CLIENT_ID=your_xiaoe_client_id
XIAOE_SECRET_KEY=your_xiaoe_secret_key

# 同步任务配置
LOG_LEVEL=INFO  # 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
ORDERS_SYNC_INTERVAL_MINUTES=30 # 订单增量同步间隔 (分钟)
STATUS_UPDATE_INTERVAL_HOURS=1 # 近期订单状态更新间隔 (小时)
STATUS_UPDATE_DAYS=15 # 状态更新扫描的天数范围
API_RETRY_TIMES=3 # API 调用失败重试次数
API_RETRY_DELAY_SECONDS=5 # API 调用重试间隔 (秒)

# 可以在这里添加其他自定义配置...
```

## 配置项说明

*   **`DATABASE_URL`**: SQLAlchemy 数据库连接字符串。请根据你的数据库类型和认证信息修改。
*   **`XIAOE_APP_ID`**: 小鹅通应用的 App ID。
*   **`XIAOE_CLIENT_ID`**: 小鹅通应用的 Client ID。
*   **`XIAOE_SECRET_KEY`**: 小鹅通应用的 Secret Key。
*   **`LOG_LEVEL`**: 应用的日志记录级别。
*   **`ORDERS_SYNC_INTERVAL_MINUTES`**: `incremental` 模式下订单同步任务的执行频率（建议与宝塔计划任务设置一致）。
*   **`STATUS_UPDATE_INTERVAL_HOURS`**: `status_update` 模式下订单状态更新任务的执行频率（建议与宝塔计划任务设置一致）。
*   **`STATUS_UPDATE_DAYS`**: 执行状态更新时，向前追溯的天数。例如，设置为 15 会检查过去 15 天内创建的订单。
*   **`API_RETRY_TIMES`**: 调用小鹅通 API 失败时的最大重试次数。
*   **`API_RETRY_DELAY_SECONDS`**: 每次重试之间的等待时间（秒）。

## 加载配置

项目通过 `config/config.py` 模块加载 `.env` 文件中的配置项到环境变量中，并在代码中通过 `os.getenv()` 或配置类访问。

```python
# 示例: config/config.py
import os
from dotenv import load_dotenv

# 获取项目根目录 (假设 config.py 在 config/ 目录下)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# .env 文件路径
dotenv_path = os.path.join(BASE_DIR, 'config', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# 通过 os.getenv 获取配置
DATABASE_URL = os.getenv('DATABASE_URL')
XIAOE_APP_ID = os.getenv('XIAOE_APP_ID')
# ... 其他配置项

# 或者封装成配置类
class Settings:
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./default.db') # 提供默认值
    XIAOE_APP_ID: str = os.getenv('XIAOE_APP_ID')
    XIAOE_CLIENT_ID: str = os.getenv('XIAOE_CLIENT_ID')
    XIAOE_SECRET_KEY: str = os.getenv('XIAOE_SECRET_KEY')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    ORDERS_SYNC_INTERVAL_MINUTES: int = int(os.getenv('ORDERS_SYNC_INTERVAL_MINUTES', 30))
    STATUS_UPDATE_INTERVAL_HOURS: int = int(os.getenv('STATUS_UPDATE_INTERVAL_HOURS', 1))
    STATUS_UPDATE_DAYS: int = int(os.getenv('STATUS_UPDATE_DAYS', 15))
    API_RETRY_TIMES: int = int(os.getenv('API_RETRY_TIMES', 3))
    API_RETRY_DELAY_SECONDS: int = int(os.getenv('API_RETRY_DELAY_SECONDS', 5))

settings = Settings()

# 在代码中导入并使用: from config.config import settings
```
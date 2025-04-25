# BI 数据同步项目 (小鹅通)

本项目用于从小鹅通平台同步用户、订单、售后和商品数据到本地数据库 (MySQL)。

## 设置步骤

1.  **创建虚拟环境:**
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # macOS/Linux
    # source ./.venv/bin/activate
    ```

2.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境变量:**
    *   复制 `.env.example` 文件为 `.env`。
    *   在 `.env` 文件中填入你的小鹅通 API 凭证:
        ```dotenv
        XIAOE_APP_ID=你的AppID
        XIAOE_CLIENT_ID=你的ClientID
        XIAOE_SECRET_KEY=你的SecretKey
        ```
    *   填入你的 MySQL 数据库连接信息:
        ```dotenv
        MYSQL_USER=你的数据库用户名
        MYSQL_PASSWORD=你的数据库密码
        MYSQL_HOST=你的数据库主机地址 (例如 localhost)
        MYSQL_PORT=你的数据库端口 (例如 3306)
        MYSQL_DB_NAME=你的数据库名称
        ```
    *   (可选) 配置同步时间范围和日志级别:
        ```dotenv
        # 拉取最近多少天的订单数据 (默认 1)
        SYNC_ORDERS_DAYS_BACK=1 
        # 拉取最近多少天的售后数据 (默认 1)
        SYNC_AFTERSALES_DAYS_BACK=1 
        # 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL, 默认 INFO)
        LOG_LEVEL=DEBUG 
        ```

4.  **(首次运行或模型更改后) 应用数据库迁移:**
    ```bash
    alembic upgrade head
    ```

## 运行同步

```bash
python -m src.main
```

日志将输出到控制台和项目根目录下的 `sync.log` 文件。

## 项目结构

```
bi_hcyj/
├── alembic/            # Alembic 数据库迁移配置和版本
├── src/                # 主应用代码目录
│   ├── xiaoe/          # 小鹅通平台模块 (API 客户端)
│   ├── database/       # 数据库交互模块 (模型, 管理器)
│   ├── core/           # 核心/通用模块 (配置, 日志, 转换器)
│   └── main.py         # 主执行脚本/同步逻辑
├── tests/              # 测试代码目录 (待完善)
├── .env.example        # 环境变量示例文件
├── .env                # 环境变量文件 (请勿提交到版本库)
├── requirements.txt    # Python 依赖列表
├── alembic.ini         # Alembic 配置文件
├── pytest.ini          # Pytest 配置文件
├── sync.log            # 日志文件
└── README.md           # 项目说明 (本文件)
``` 
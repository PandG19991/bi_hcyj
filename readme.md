# 多平台 BI 数据同步系统 (MVP - 小鹅通)

本项目旨在将小鹅通平台的订单、用户、商品数据同步到 MySQL 数据库，并特别关注订单创建后 14 天内的状态更新，以满足业务需求。

## 功能特性 (MVP)

*   同步小鹅通订单、用户、商品核心数据至 MySQL。
*   定期检查并更新近期（默认 15 天内）订单的状态。
*   基于时间戳的增量同步。
*   基本的错误处理和 API 调用重试。
*   支持在宝塔面板通过计划任务运行。
*   提供基础的文件日志记录。

## 技术栈

*   Python 3.9+ (本项目使用 Python 3.12 测试通过)
*   MySQL 5.7.44+ (兼容，但推荐使用 MySQL 8.0+)
*   SQLAlchemy ~=1.4 (ORM)
*   Requests (HTTP 请求)
*   python-dotenv (配置管理)

## 项目结构

```
/data_sync/
├── config/           # 配置目录 (.env, config.py)
├── core/             # 核心逻辑 (db, loaders, models)
├── platforms/xiaoe/  # 小鹅通模块 (client, transformers)
├── utils/            # 工具 (logger, retry)
├── logs/             # 日志输出目录
├── scripts/          # 入口脚本 (sync_xiaoe.py)
├── requirements.txt  # 依赖
├── README.md         # 本文档
└── docs/             # 其他文档 (database, config, deployment)
```

## 快速开始

**1. 克隆仓库:**

```bash
git clone <your-repository-url>
cd data_sync
```

**2. 配置环境:**

*   参考 `docs/config.md` 创建并编辑 `config/.env` 文件，填入数据库连接信息和小鹅通 API Key/Secret。
*   确保已安装 Python 3.9+ (推荐 3.12) 和 MySQL 5.7.44+。

**3. 安装依赖:**

```bash
# 建议使用 Python 3.12
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install pymysql # 确保驱动已安装
```

**4. 初始化数据库:**

*   手动连接到你的 MySQL 数据库 (支持 5.7.44+)。
*   执行 `docs/database.md` 中的 SQL 语句来创建所需的表。

**5. 手动运行同步 (用于测试):**

```bash
# 运行增量同步 (拉取新订单)
py -3.12 scripts/sync_xiaoe.py --sync-type incremental

# 运行状态更新 (更新近期订单状态)
py -3.12 scripts/sync_xiaoe.py --sync-type status_update

# 注意：首次运行建议先运行 incremental，再运行 status_update
```

**6. 部署到宝塔面板:**

*   参考 `docs/deployment.md` 进行部署和配置计划任务。

## 文档

*   [数据库 Schema](./docs/database.md)
*   [配置说明](./docs/config.md)
*   [部署指南](./docs/deployment.md)

## 日志

*   日志文件默认输出到项目根目录下的 `logs/` 文件夹中。
*   可在 `config/.env` 文件中通过 `LOG_LEVEL` 变量调整日志级别。

## 注意事项

*   请务必保护好 `config/.env` 文件中的敏感信息。
*   定期检查日志文件，关注 `ERROR` 或 `CRITICAL` 级别的日志。
*   根据小鹅通 API 的限制调整同步频率和请求逻辑。
*   本项目代码已在 Python 3.12 和 MySQL 8.0 环境下测试通过，并确认兼容 MySQL 5.7.44+。
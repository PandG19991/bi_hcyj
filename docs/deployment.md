# 部署指南 (宝塔面板 - MVP)

本指南说明如何将项目部署到已安装宝塔面板的 Linux 服务器上。

## 前提条件

1.  **服务器:** 一台 Linux 服务器 (推荐 CentOS 7+ 或 Ubuntu 18.04+)。
2.  **宝塔面板:** 已在服务器上安装并正常运行。
3.  **MySQL:** 已通过宝塔面板安装 MySQL 数据库。本项目兼容 MySQL 5.7.44+，但**强烈推荐使用 MySQL 8.0+** (如果可用)，因为它拥有更好的性能和安全性。请创建好项目所需的数据库和用户，并记下数据库名、用户名和密码。
4.  **Python:** 服务器上安装了 Python 3.9 或更高版本 (推荐使用 3.12，如果宝塔 Python 项目管理器支持)。可以通过宝塔面板的 "软件商店" -> "运行环境" 安装 Python 项目管理器，并创建一个合适的 Python 版本环境。
5.  **Git:** 服务器上安装了 Git。

## 部署步骤

**1. 上传代码:**

*   登录服务器。
*   使用 Git 克隆项目代码到服务器上的指定目录（例如 `/www/wwwroot/data_sync`）：
    ```bash
    cd /www/wwwroot
    git clone <your-repository-url> data_sync
    cd data_sync
    ```
    或者，将本地代码打包上传到服务器 `/www/wwwroot/data_sync` 目录并解压。

**2. 配置 Python 环境 (推荐使用宝塔的 Python 项目管理器):**

*   打开宝塔面板，进入 "软件商店" -> "运行环境" -> "Python 项目管理器"。
*   点击 "添加项目"，项目路径选择 `/www/wwwroot/data_sync`。
*   选择合适的 Python 版本 (推荐 3.12，最低 3.9)。
*   框架选择 "通用"。
*   启动方式选择 "python"。
*   启动文件留空或不填。
*   点击 "确定"。
*   进入项目管理界面，点击 "依赖包管理"，选择 "pip install -r requirements.txt"，点击 "安装"。等待依赖安装完成。
*   如果数据库使用 MySQL，确保 `pymysql` 也被安装 (可以手动在项目管理器的终端中运行 `pip install pymysql`)。

**3. 配置 `.env` 文件:**

*   在服务器上，进入项目目录 `/www/wwwroot/data_sync/config`。
*   复制一份 `.env.example` (如果提供了) 或直接创建 `.env` 文件。
*   编辑 `.env` 文件，填入正确的数据库连接信息 (`DATABASE_URL`) 和小鹅通 API 密钥 (`XIAOE_APP_ID`, `XIAOE_CLIENT_ID`, `XIAOE_SECRET_KEY`)。
    ```bash
    cd /www/wwwroot/data_sync/config
    # cp .env.example .env  (如果存在模板)
    vim .env # 或者使用宝塔的文件管理器在线编辑
    ```
*   **重要:** 确保 `.env` 文件权限安全，例如设置为 `600`，只有运行脚本的用户可读写。

**4. 初始化数据库:**

*   通过宝塔面板的 "数据库" 功能或 SSH 登录 MySQL。
*   执行 `docs/database.md` 中的 SQL 脚本，创建所需的表。

**5. 测试运行 (可选但推荐):**

*   通过 SSH 登录服务器。
*   进入项目目录 `/www/wwwroot/data_sync`。
*   激活 Python 项目管理器创建的虚拟环境（如果需要，或者直接使用项目管理器提供的 Python 路径）。
    ```bash
    cd /www/wwwroot/data_sync
    # 例如，获取 Python 解释器路径 (请根据实际情况查找!)
    # PYTHON_EXEC=/www/server/pyenv/versions/<your-python-env-name>/bin/python
    # $PYTHON_EXEC scripts/sync_xiaoe.py --sync-type incremental
    # 或者如果宝塔环境已设置好路径
    python scripts/sync_xiaoe.py --sync-type incremental # 测试增量同步
    ```
*   检查 `logs/` 目录下的日志文件，确认没有错误。
*   检查数据库，确认数据已正确写入。

**6. 配置宝塔计划任务:**

*   登录宝塔面板，进入 "计划任务"。
*   **任务类型:** 选择 "Shell脚本"。
*   **任务名称:** 例如 "小鹅通订单增量同步"。
*   **执行周期:** 根据需求设置 (例如 "每 30 分钟")。
*   **脚本内容:**
    ```bash
    #!/bin/bash
    PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
    export PATH

    # **重要:** 宝塔 Python 项目管理器创建的 Python 解释器路径 (务必根据实际情况修改!)
    # 在宝塔项目管理器设置页面可以找到，或者通过 which python 查看
    PYTHON_EXEC=/www/server/pyenv/versions/<your-python-env-name>/bin/python
    # 项目脚本路径
    SCRIPT_PATH=/www/wwwroot/data_sync/scripts/sync_xiaoe.py
    # 项目根目录
    PROJECT_DIR=/www/wwwroot/data_sync
    # 日志文件
    LOG_FILE=$PROJECT_DIR/logs/cron_incremental.log # 使用变量更清晰

    echo "--------------------" >> $LOG_FILE
    echo "Task started at: $(date)" >> $LOG_FILE
    # 使用指定的 Python 解释器执行脚本，切换到项目目录以确保相对路径正确
    cd $PROJECT_DIR && $PYTHON_EXEC $SCRIPT_PATH --sync-type incremental >> $LOG_FILE 2>&1
    echo "Task finished at: $(date)" >> $LOG_FILE
    echo "--------------------" >> $LOG_FILE
    ```
    *   再次强调：务必将 `<your-python-env-name>` 替换为你在宝塔 Python 项目管理器中设置的环境名称或找到正确的 `python` 可执行文件路径。

*   **添加第二个计划任务:** 用于订单状态更新。
    *   **任务名称:** 例如 "小鹅通订单状态更新"。
    *   **执行周期:** 例如 "每小时"。
    *   **脚本内容:** 与上面类似，但修改 `--sync-type` 参数和日志文件名：
        ```bash
        # ... (前面的 PATH 和变量定义相同) ...
        LOG_FILE=$PROJECT_DIR/logs/cron_status_update.log
        # ...
        cd $PROJECT_DIR && $PYTHON_EXEC $SCRIPT_PATH --sync-type status_update >> $LOG_FILE 2>&1
        # ...
        ```

*   点击 "添加任务"。

**7. 监控与维护:**

*   **检查任务执行日志:** 定期查看宝塔计划任务的执行日志（点击任务后的 "日志" 按钮）以及脚本自身输出到 `logs/` 目录下的日志文件 (`cron_incremental.log`, `cron_status_update.log`)。
*   **检查数据库数据:** 定期抽查数据库中的数据，确认同步的准确性和及时性。
*   **宝塔面板监控:** 利用宝塔面板的系统负载、CPU、内存监控，观察脚本运行期间的资源消耗。
*   **代码更新:** 如果需要更新代码，使用 `git pull` 更新代码，如果依赖有变化，重新执行 `pip install -r requirements.txt`。

## 注意事项

*   **Python 路径:** 宝塔计划任务中 Python 解释器的路径 (`PYTHON_EXEC`) 至关重要，务必填写正确。
*   **文件权限:** 确保运行计划任务的用户（通常是 `www` 或 `root`）对项目目录、脚本、日志文件有读写执行权限。
*   **环境变量:** 宝塔计划任务默认可能不会加载用户的 `.bashrc` 或 `.profile`，因此直接在脚本中指定 Python 完整路径比依赖 `PATH` 更可靠。`.env` 文件由 Python 脚本内部加载，不受此影响。
*   **日志轮转:** 对于长期运行的任务，需要配置日志轮转（例如使用 Linux 的 `logrotate` 工具或 Python 的 `logging.handlers.RotatingFileHandler`）以防止日志文件无限增大。MVP 阶段可以暂时手动清理。

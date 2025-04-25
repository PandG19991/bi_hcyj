# 开发任务计划

**阶段 0: 环境与工具准备 (Setup)**

*   **任务:**
    1.  初始化 Git 仓库 (`git init`)。
    2.  创建 `.gitignore` 文件，忽略不必要的文件（如 `__pycache__`, `.env`, 虚拟环境目录等）。
    3.  设置 Python 虚拟环境 (e.g., `python -m venv .venv`) 并激活。
    4.  在 `requirements.txt` 中添加基础依赖 (如 `python-dotenv`, `requests`) 并安装 (`pip install -r requirements.txt`)。
    5.  配置开发工具（IDE/编辑器）以使用 Black, Flake8/Pylint, MyPy，并遵循 `.cursor/rules/coding-standards.mdc`。
*   **测试:**
    *   确认虚拟环境工作正常。
    *   确认基础依赖已安装。
    *   手动运行 Black, Flake8/Pylint 对已有占位符文件进行检查，确保工具配置无误。

**阶段 1: 核心组件与配置 (Core & Config)**

*   **任务:**
    1.  在 `example/config.py` 中定义配置变量结构 (API Keys, DB Credentials)。考虑使用 `.env` 文件配合 `python-dotenv` 加载敏感信息到环境变量，`config.py` 则从环境变量读取。
    2.  在 `src/core/utils.py` (或新建 `src/core/config.py`) 中实现配置加载逻辑。
    3.  在 `src/core/utils.py` (或新建 `src/core/logger.py`) 中设置基本的日志记录器 (使用 `logging` 模块)，配置日志格式和输出（控制台/文件）。
*   **测试:**
    *   **单元测试:**
        *   测试配置加载函数能否正确读取 `example/config.py` 或环境变量。
        *   测试日志记录器能否被正确初始化并输出预期格式的日志。

**阶段 2: 数据库集成 (Database Integration)**

*   **任务:**
    1.  确定 ORM (推荐 SQLAlchemy) 并在 `requirements.txt` 中添加依赖 (`SQLAlchemy`, `psycopg2-binary` 或 `mysql-connector-python`) 并安装。
    2.  在 `src/database/manager.py` 中实现数据库连接逻辑 (连接池)，从配置中读取凭证。
    3.  在 `src/database/models.py` 中使用 ORM 定义初步的数据表模型 (例如，一个通用的 `SyncRecord` 表，或者根据小鹅通数据定义 `XiaoeUser` 表等)。
    4.  (推荐) 配置数据库迁移工具 (如 Alembic)，创建初始数据库模式迁移脚本。
*   **测试:**
    *   **集成测试:**
        *   编写测试用例，验证 `DatabaseManager` 能否成功连接到**测试数据库** (使用单独的测试数据库配置)。
        *   (如果使用迁移工具) 运行迁移脚本，验证表结构是否在测试数据库中正确创建。
        *   编写测试用例，尝试通过 `DatabaseManager` 对测试数据库进行简单的写入和读取操作 (例如，写入一条测试记录并读回验证)。

**阶段 3: 小鹅通 API 客户端实现 (Xiaoe Client)**

*   **任务:**
    1.  在 `src/xiaoe/client.py` 中实现 `XiaoeClient` 类。
    2.  实现身份验证逻辑（基于 `config.py` 中的 AppID, ClientID, SecretKey）。
    3.  实现至少一个核心数据获取方法（例如 `get_users_list(page, page_size)`），处理 API 请求发送和响应解析 (JSON)。
    4.  添加基本的 API 错误处理（网络错误、API 返回错误码等）。
    5.  (可选) 定义 Pydantic 模型来验证和解析 API 响应数据结构。
*   **测试:**
    *   **单元测试:**
        *   使用 `unittest.mock` 模拟 `requests` 库，测试 `XiaoeClient` 的身份验证逻辑是否按预期工作（构造正确的请求参数、处理模拟的成功/失败响应）。
        *   测试数据获取方法，模拟 API 成功响应和各种错误响应（如 4xx, 5xx 错误，空数据等），验证客户端是否能正确处理并返回/抛出异常。
        *   (如果使用 Pydantic) 测试模型能否正确解析模拟的 API 响应数据。

**阶段 4: 小鹅通数据同步与存储 (Xiaoe Sync & Store)**

*   **任务:**
    1.  在 `src/database/models.py` 中完善小鹅通相关的数据模型。
    2.  在 `src/database/manager.py` 中实现将处理后的小鹅通数据写入数据库的方法（例如 `save_xiaoe_users(users_data)`），注意处理数据重复/更新（幂等性）。
    3.  在 `src/main.py` 中编排同步流程：
        *   加载配置。
        *   初始化 `XiaoeClient` 和 `DatabaseManager`。
        *   调用 `XiaoeClient` 获取数据。
        *   (如果需要) 进行数据转换/清洗。
        *   调用 `DatabaseManager` 保存数据。
        *   添加详细的日志记录。
*   **测试:**
    *   **单元测试:**
        *   测试 `DatabaseManager` 中数据保存方法的逻辑（模拟输入数据，验证对数据库操作的调用，或直接操作内存数据库如 SQLite 进行测试）。测试幂等性逻辑。
    *   **集成测试:**
        *   编写测试用例，模拟 `XiaoeClient` 返回预设的测试数据，然后调用 `main.py` 中的同步逻辑，验证数据是否正确写入**测试数据库**。
        *   再次运行相同的集成测试，验证幂等性（数据库状态应与第一次运行后相同）。

**阶段 5 & 6: 接入其他平台 (Douyin, WeChat Channels, etc.)**

*   **任务:** (对每个新平台重复)
    1.  创建平台模块目录 (e.g., `src/douyin/`) 及 `client.py`。
    2.  实现对应的 `PlatformClient` (遵循统一接口设计)。
    3.  实现认证、数据获取、错误处理。
    4.  如有必要，在 `src/database/models.py` 添加/修改数据模型，并生成数据库迁移脚本。
    5.  在 `src/database/manager.py` 添加数据存储方法。
    6.  更新 `src/main.py` 以包含新平台的同步逻辑（考虑通过配置开关控制同步哪些平台）。
*   **测试:** (对每个新平台重复)
    *   **单元测试:** 针对新平台的 `Client` 进行测试 (mock API)。
    *   **单元测试:** 针对新平台的 `DatabaseManager` 方法进行测试。
    *   **集成测试:** 针对新平台的同步流程进行测试 (mock Client, test DB)。

**阶段 7: 完善与部署准备 (Refinement & Deployment)**

*   **任务:**
    1.  代码审查与重构，提升代码质量和可读性。
    2.  完善错误处理和日志记录。
    3.  编写/更新 `README.md`，包含项目介绍、环境设置、配置说明、运行方式等。
    4.  (推荐) 使用 Sphinx 根据 Docstrings 生成项目文档。
    5.  编写 `Dockerfile` 和 `docker-compose.yml` 实现容器化。
    6.  (推荐) 配置 CI/CD 流水线，自动运行测试、代码检查，甚至构建 Docker 镜像。
*   **测试:**
    *   检查测试覆盖率报告，补充关键逻辑的测试用例。
    *   进行手动端到端测试（如果条件允许，连接 Staging 环境 API 和数据库）。
    *   测试 Docker 构建和容器运行是否正常。
    *   测试 CI/CD 流水线是否按预期工作。

这个计划提供了一个清晰的、循序渐进的开发路径，并强调了在每个阶段进行测试的重要性，有助于保证最终产品的质量和稳定性。您可以根据实际情况调整每个阶段的具体任务和时间安排。


## MVP 阶段规划建议

我们可以将 MVP 的实现大致分为以下几个阶段，每个阶段都有其核心目标：

**阶段 1: 项目初始化与核心基础设施 (目标：搭建骨架)**

*   **任务:**
    *   创建 `README.md`, `.gitignore` 文件。
    *   创建 `docs/` 目录及核心 Markdown 文件 (`database.md`, `config.md`, `deployment.md`) 的初始框架。
    *   创建完整的项目目录结构（包括 `config/`, `core/`, `platforms/xiaoe/`, `utils/`, `logs/`, `scripts/` 以及所有必要的 `__init__.py` 文件）。
    *   实现配置加载 (`config/config.py`, `config/.env.example`)。
    *   实现基础日志配置 (`utils/logger.py`)。
    *   实现数据库连接和会话管理 (`core/db.py`)。
*   **产出:** 一个包含基础配置、日志、数据库连接功能的空项目骨架，结构清晰。

**阶段 2: 数据模型与基础加载器 (目标：定义数据存储)**

*   **任务:**
    *   根据 `docs/database.md` 在 `core/models.py` 中定义 SQLAlchemy 模型 (`Order`, `OrderItem`, `User`, `Product`, `SyncStatus`)。
    *   实现 `core/loaders.py` 中的基础 UPSERT 函数，能够将 Python 对象（字典或模型实例）写入对应的数据库表。
    *   （可选）编写简单的测试脚本验证模型定义和基础加载功能。
*   **产出:** 定义好的数据模型和能够将数据写入数据库的基础加载逻辑。

**阶段 3: 小鹅通 API 对接与数据转换 (目标：获取并处理原始数据)**

*   **任务:**
    *   在 `platforms/xiaoe/client.py` 中实现获取订单、用户、商品列表的核心 API 调用逻辑（包括认证、分页、错误处理、重试）。
    *   在 `platforms/xiaoe/transformers.py` 中实现将 API 返回的原始数据转换为 `core/models.py` 中定义的模型对象或对应字典结构（处理字段映射、数据类型转换、单位转换等）。
*   **产出:** 能够从 小鹅通 API 获取数据并将其转换为标准内部格式的模块。

**阶段 4: 核心同步逻辑实现 (目标：打通数据流)**

*   **任务:**
    *   在 `scripts/sync_xiaoe.py` 或相关核心模块中，实现**增量同步**逻辑：
        *   从 `sync_status` 表读取上次同步时间戳。
        *   调用 `client` 获取新数据。
        *   调用 `transformers` 转换数据。
        *   调用 `loaders` 将数据写入数据库。
        *   更新 `sync_status` 表。
    *   实现**状态更新**逻辑：
        *   查询过去 15 天创建的订单 ID。
        *   分批调用 `client` 获取这些订单的最新状态（可能需要调用不同的 API 端点，或者在获取列表时检查）。
        *   调用 `transformers` 转换数据。
        *   调用 `loaders` 更新数据库中对应订单的状态字段。
        *   更新 `sync_status` 表。
*   **产出:** 能够执行增量同步和状态更新核心流程的脚本。

**阶段 5: 任务调度与部署准备 (目标：自动化与可部署)**

*   **任务:**
    *   （如果需要脚本内调度）在 `core/scheduler.py` 中使用 `APScheduler` 配置定时任务，调用阶段 4 的同步逻辑。
    *   完善 `scripts/sync_xiaoe.py` 的命令行参数处理 (例如 `--sync-type`)。
    *   最终确定并完善 `docs/deployment.md` 中的宝塔面板部署和计划任务配置步骤。
*   **产出:** 可以通过命令行手动运行，并已准备好通过宝塔计划任务自动执行的同步脚本，以及最终的部署文档。

**阶段 6: 测试、优化与文档完善 (目标：稳定交付)**

*   **任务:**
    *   进行端到端的测试，模拟各种场景（首次运行、增量、状态更新、API 错误等）。
    *   根据测试结果进行 Bug 修复和必要的逻辑优化。
    *   完善所有 `docs/` 目录下的文档和 `README.md`。
*   **产出:** 一个经过测试、相对稳定可靠、文档齐全的 MVP 版本。

# core/loaders.py
from typing import List, Dict, Any, Type
from sqlalchemy.dialects.mysql import insert as mysql_insert # MySQL specific insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.db import get_db, Base # 导入数据库会话获取函数和 Base
from utils.logger import logger

# 定义一个类型别名，表示数据项可以是字典或模型实例
DataItem = Dict[str, Any] | Base

def upsert_data(db: Session, model_class: Type[Base], data_list: List[DataItem]):
    """
    将数据批量 UPSERT (Insert or Update) 到指定的数据库表中。

    Args:
        db: SQLAlchemy 数据库会话。
        model_class: 要操作的 SQLAlchemy 模型类 (继承自 Base)。
        data_list: 包含数据项的列表，每个数据项可以是字典或模型实例。
    """
    if not data_list:
        logger.info(f"No data provided for upsert into {model_class.__tablename__}. Skipping.")
        return

    table = model_class.__table__
    total_count = len(data_list)

    logger.info(f"Starting upsert for {total_count} records into {model_class.__tablename__}...")

    try:
        # 1. 准备插入语句
        # 为了同时支持字典和模型实例，我们先将它们统一转换为字典列表
        values_list = []
        valid_count = 0
        for item in data_list:
            if isinstance(item, dict):
                # 过滤字典，只包含模型中存在的列
                filtered_item = {c.name: item.get(c.name) for c in table.columns if c.name in item}
                values_list.append(filtered_item)
                valid_count += 1
            elif isinstance(item, Base) and isinstance(item, model_class):
                # 将模型实例转换为字典
                instance_dict = {c.name: getattr(item, c.name, None) for c in table.columns}
                values_list.append(instance_dict)
                valid_count += 1
            else:
                logger.warning(f"Skipping invalid data item type or mismatch: {type(item)} for model {model_class.__name__}")

        if not values_list:
            logger.warning(f"No valid data items found for upsert into {model_class.__tablename__} after filtering.")
            return

        logger.info(f"Processing {valid_count} valid data items for {model_class.__tablename__}.")

        stmt = mysql_insert(table).values(values_list)

        # 2. 准备 ON DUPLICATE KEY UPDATE 部分
        # 获取非主键的列名用于更新
        update_columns = {
            c.name: stmt.inserted[c.name]
            for c in table.columns
            if not c.primary_key
            # updated_at 通常由数据库 onupdate 触发器处理，无需在此指定
            # and c.name != 'created_at' # 通常不更新创建时间
        }

        # 如果没有非主键列（仅有主键的表），则执行简单更新（或忽略）
        if not update_columns:
             # MySQL's ON DUPLICATE KEY UPDATE requires at least one assignment.
             # Assign a primary key to itself as a no-op to satisfy syntax.
             pk_col_name = next(iter(table.primary_key.columns)).name
             upsert_stmt = stmt.on_duplicate_key_update({pk_col_name: stmt.inserted[pk_col_name]})
             logger.warning(f"No non-primary key columns to update for table {model_class.__tablename__}. Using dummy update on PK.")
             # 备选方案：如果想忽略重复项而不是更新:
             # upsert_stmt = mysql_insert(table).prefix_with('IGNORE').values(values_list)
        else:
            # 构建 UPSERT 语句
            upsert_stmt = stmt.on_duplicate_key_update(**update_columns)


        # 3. 执行语句
        result = db.execute(upsert_stmt)

        # 4. 处理结果 (MySQL 的 rowcount 行为比较特殊)
        affected_rows = result.rowcount
        logger.info(f"UPSERT statement executed for {model_class.__tablename__}. Approx affected rows: {affected_rows}")
        # Note: affected_rows = 1 for insert, 2 for update, 0 for no change.

        # 5. 提交事务
        db.commit()
        logger.info(f"Successfully upserted data into {model_class.__tablename__}. Processed {valid_count} items. Transaction committed.")

    except SQLAlchemyError as e:
        logger.error(f"Database error during upsert into {model_class.__tablename__}: {e}", exc_info=True)
        db.rollback() # 发生错误时回滚事务
        logger.warning(f"Transaction rolled back for {model_class.__tablename__}.")
        raise # 重新抛出异常，让上层处理
    except Exception as e:
        logger.error(f"Unexpected error during upsert into {model_class.__tablename__}: {e}", exc_info=True)
        db.rollback()
        logger.warning(f"Transaction rolled back for {model_class.__tablename__}.")
        raise

# --- 使用示例 (仅作演示，通常在同步脚本中调用) ---
# if __name__ == "__main__":
#     from core.models import User # 假设 User 模型已定义
#     from datetime import datetime, timezone
#     from core.db import test_db_connection, SessionLocal, engine, Base
#
#     logger.info("Running loader example...")
#
#     # 如果表不存在，先创建表 (仅用于测试)
#     # logger.info("Ensuring tables exist...")
#     # Base.metadata.create_all(bind=engine)
#
#     # 先测试数据库连接
#     if not test_db_connection():
#          logger.error("Database connection failed. Aborting example.")
#          exit()
#
#     # 准备一些示例数据 (字典格式)
#     sample_users = [
#         # Existing user, nickname will be updated
#         {'platform': 'xiaoe', 'user_id': 'user_001', 'nickname': 'Alice_V5', 'register_time': datetime.now(timezone.utc), 'mobile': '111'},
#         # New user
#         {'platform': 'xiaoe', 'user_id': 'user_005', 'nickname': 'Eve', 'register_time': datetime.now(timezone.utc)},
#         # Existing user, mobile will be updated
#         {'platform': 'xiaoe', 'user_id': 'user_003', 'nickname': 'Charlie_V2', 'mobile': '13800000005'},
#         # Invalid data type (should be skipped)
#         12345,
#         # Data with extra fields (should be handled by filtering in upsert)
#         {'platform': 'xiaoe', 'user_id': 'user_006', 'nickname': 'Frank', 'extra_field': 'ignore_me'}
#     ]
#
#     # 获取数据库会话
#     session = SessionLocal()
#
#     try:
#         # 第一次插入/更新
#         logger.info("--- First Upsert Run ---")
#         upsert_data(session, User, sample_users)
#         logger.info("First upsert run finished.")
#
#         # 第二次插入/更新 (验证更新逻辑)
#         logger.info("--- Second Upsert Run (Updating Eve) ---")
#         upsert_data(session, User, [
#             {'platform': 'xiaoe', 'user_id': 'user_005', 'nickname': 'Eve_Updated', 'mobile': '222'}
#         ])
#         logger.info("Second upsert run finished.")
#
#         # 验证数据 (可选)
#         logger.info("--- Verifying Data ---")
#         user1 = session.query(User).filter_by(platform='xiaoe', user_id='user_001').first()
#         if user1: logger.info(f"Verified user 1: {user1.nickname} (Should be Alice_V5)")
#         user5 = session.query(User).filter_by(platform='xiaoe', user_id='user_005').first()
#         if user5: logger.info(f"Verified user 5: {user5.nickname} (Should be Eve_Updated), Mobile: {user5.mobile}")
#         user6 = session.query(User).filter_by(platform='xiaoe', user_id='user_006').first()
#         if user6: logger.info(f"Verified user 6: {user6.nickname} (Should be Frank)")
#
#
#     except Exception as e:
#         logger.error(f"An error occurred in the example: {e}", exc_info=True)
#     finally:
#         # 关闭会话
#         session.close()
#         # db_session.remove() # 如果使用 scoped_session，可以用 remove()
#         logger.info("Database session closed.")
# core/loaders.py
from typing import List, Dict, Any, Type, Union
from sqlalchemy.dialects.mysql import insert as mysql_insert # MySQL specific insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete
from collections import defaultdict

from core.db import get_db, Base # 导入数据库会话获取函数和 Base
from utils.logger import logger
from core.models import Order, AftersaleOrder, AftersaleItem, OrderItem # 导入所需模型

# 定义输入数据的可能类型：字典或 SQLAlchemy 模型实例
DataItem = Union[Dict[str, Any], Base] # 使用 Union

ModelType = Type[Base] # 类型提示，表示模型类本身

def upsert_data(db: Session, model_class: ModelType, data_list: List[DataItem]):
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

        logger.info(f"Successfully executed upsert statement for {model_class.__tablename__}. Processed {valid_count} items. Commit should happen in caller.")

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

# --- 特定模型的加载器 --- 

def upsert_aftersale_orders_with_user_lookup(db: Session, aftersale_orders_data: List[Dict[str, Any]]):
    """
    Upserts AftersaleOrder records, automatically looking up the user_id from the related Order.

    Args:
        db: SQLAlchemy 数据库会话。
        aftersale_orders_data: List of transformed aftersale order dictionaries.
    """
    if not aftersale_orders_data:
        logger.info("No aftersale order data provided for upsert. Skipping.")
        return

    processed_data = []
    order_ids = {d['order_id']: d['platform'] for d in aftersale_orders_data if 'order_id' in d and 'platform' in d}

    # 批量查询关联订单的 user_id
    user_id_map = {}
    if order_ids:
        try:
            # 构建查询条件，支持复合主键
            order_query = db.query(Order.order_id, Order.platform, Order.user_id)\
                            .filter(tuple_(Order.platform, Order.order_id).in_([(p, o) for o, p in order_ids.items()]))
            results = order_query.all()
            for platform, order_id, user_id in results:
                user_id_map[(platform, order_id)] = user_id
            logger.info(f"Fetched user_ids for {len(user_id_map)} associated orders.")
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user_ids for orders: {e}", exc_info=True)
            # 如果查询失败，可以选择继续（user_id 为 None）或抛出异常
            # 这里选择继续

    # 准备最终数据，填充 user_id
    for data in aftersale_orders_data:
        platform = data.get('platform')
        order_id = data.get('order_id')
        aftersale_id = data.get('aftersale_id')

        if not platform or not order_id or not aftersale_id:
            logger.warning(f"Skipping aftersale order due to missing platform, order_id, or aftersale_id: {data}")
            continue

        # 从 map 获取 user_id
        data['user_id'] = user_id_map.get((platform, order_id))
        if data['user_id'] is None:
            logger.warning(f"Could not find user_id for aftersale order {aftersale_id} (order_id: {order_id}, platform: {platform}). Setting user_id to NULL.")

        processed_data.append(data)

    if not processed_data:
        logger.warning("No processable aftersale order data found after user_id lookup.")
        return

    # 调用通用的 upsert 函数
    logger.info(f"Calling upsert_data for {len(processed_data)} AftersaleOrder records.")
    upsert_data(db, AftersaleOrder, processed_data)

def replace_aftersale_items(db: Session, aftersale_items_data: List[Dict[str, Any]]):
    """
    Replaces (deletes then inserts) AftersaleItem records for the given aftersale_ids.

    Args:
        db: SQLAlchemy 数据库会话。
        aftersale_items_data: List of transformed aftersale item dictionaries.
                               Must contain 'aftersale_id' and 'platform'.
    """
    if not aftersale_items_data:
        logger.info("No aftersale item data provided for replacement. Skipping.")
        return

    # 按 (platform, aftersale_id) 分组数据
    grouped_items = defaultdict(list)
    aftersale_ids_to_process = set()
    valid_items_count = 0

    for item in aftersale_items_data:
        platform = item.get('platform')
        aftersale_id = item.get('aftersale_id')
        if platform and aftersale_id:
            key = (platform, aftersale_id)
            grouped_items[key].append(item)
            aftersale_ids_to_process.add(key)
            valid_items_count += 1
        else:
            logger.warning(f"Skipping aftersale item due to missing platform or aftersale_id: {item}")

    if not aftersale_ids_to_process:
        logger.warning("No valid aftersale items with platform and aftersale_id found for replacement.")
        return

    logger.info(f"Starting replacement for {valid_items_count} AftersaleItem records across {len(aftersale_ids_to_process)} aftersale orders.")

    try:
        # 1. 删除现有项目
        if aftersale_ids_to_process:
            # 构建删除条件
            # delete_stmt = delete(AftersaleItem)\
            #                .where(tuple_(AftersaleItem.platform, AftersaleItem.aftersale_id).in_(aftersale_ids_to_process))

            # 考虑到性能和可能的锁定问题，分批删除或逐个 aftersale_id 删除可能更好
            # 这里采用逐个 aftersale_id 删除
            deleted_count_total = 0
            for platform, aftersale_id in aftersale_ids_to_process:
                delete_stmt = delete(AftersaleItem)\
                                .where(AftersaleItem.platform == platform)\
                                .where(AftersaleItem.aftersale_id == aftersale_id)
                result = db.execute(delete_stmt)
                deleted_count_total += result.rowcount
                # logger.debug(f"Deleted {result.rowcount} existing items for aftersale_id: {aftersale_id} ({platform}).")
            logger.info(f"Deleted {deleted_count_total} existing AftersaleItem records for {len(aftersale_ids_to_process)} aftersale orders.")

        # 2. 插入新项目
        # 准备要插入的数据列表 (只包含有效字段)
        all_items_to_insert = []
        table_columns = {c.name for c in AftersaleItem.__table__.columns}
        for key in grouped_items:
            for item_dict in grouped_items[key]:
                filtered_item = {k: v for k, v in item_dict.items() if k in table_columns}
                all_items_to_insert.append(filtered_item)

        if all_items_to_insert:
            # 使用 bulk_insert_mappings 以获得更好的性能
            db.bulk_insert_mappings(AftersaleItem, all_items_to_insert)
            logger.info(f"Bulk inserted {len(all_items_to_insert)} new AftersaleItem records.")
        else:
             logger.info("No new AftersaleItem records to insert.")

        # 3. 提交事务
        # db.commit()
        logger.info(f"Successfully executed delete and insert for AftersaleItem data for {len(aftersale_ids_to_process)} aftersale orders. Commit should happen in caller.")

    except SQLAlchemyError as e:
        logger.error(f"Database error during replacing AftersaleItem data: {e}", exc_info=True)

def upsert_order_with_items(db: Session, order_data: Dict[str, Any], order_items_data: List[Dict[str, Any]]):
    """
    Upserts an Order record and replaces its associated OrderItem records.

    This function first upserts the main order details using the generic upsert_data.
    Then, it deletes all existing OrderItems for that specific order.
    Finally, it inserts the new list of OrderItems.

    Args:
        db: SQLAlchemy 数据库会话。
        order_data: A dictionary representing the Order record.
        order_items_data: A list of dictionaries representing the OrderItem records.
    """
    if not order_data or 'platform' not in order_data or 'order_id' not in order_data:
        logger.error("Cannot upsert order with items: order_data is invalid or missing platform/order_id.")
        return # Or raise ValueError?

    platform = order_data['platform']
    order_id = order_data['order_id']

    try:
        # Step 1: Upsert the Order record itself
        logger.debug(f"Upserting Order record for {platform}/{order_id}...")
        # Use upsert_data for the single order. Ensure it doesn't commit prematurely if called outside a transaction.
        # Note: upsert_data currently commits inside. For atomicity, it might be better
        # to extract the core logic or modify upsert_data to optionally not commit.
        # For MVP, we'll assume the commit inside upsert_data is acceptable, 
        # although ideally delete+insert should be in the same transaction as order upsert.
        upsert_data(db, Order, [order_data]) # Pass as a list
        logger.debug(f"Order record {platform}/{order_id} upserted.")

        # Step 2: Delete existing OrderItems for this order
        logger.debug(f"Deleting existing OrderItems for order {platform}/{order_id}...")
        delete_stmt = delete(OrderItem).where(
            OrderItem.platform == platform,
            OrderItem.order_id == order_id
        )
        delete_result = db.execute(delete_stmt)
        deleted_count = delete_result.rowcount
        logger.debug(f"Deleted {deleted_count} existing OrderItem records for order {platform}/{order_id}.")
        # Need to commit the deletion before inserting new items if upsert_data commits internally
        # db.commit() # Uncomment if necessary due to upsert_data's internal commit

        # Step 3: Insert new OrderItems if any
        if order_items_data:
            logger.debug(f"Inserting {len(order_items_data)} new OrderItems for order {platform}/{order_id}...")
            # Assuming upsert_data handles bulk insertion correctly
            # If OrderItem has its own primary key beyond (platform, order_id), upsert is fine.
            # If only (platform, order_id, some_item_key) is PK, simple insert after delete is better.
            # Let's use upsert_data for consistency, assuming it handles OrderItem PKs.
            upsert_data(db, OrderItem, order_items_data)
            logger.debug(f"New OrderItems for order {platform}/{order_id} inserted/updated.")
        else:
            logger.info(f"No new order items provided for order {platform}/{order_id}. Only order record was upserted.")

        # The main transaction commit happens in the calling function (e.g., run_incremental_sync)
        # However, due to upsert_data's internal commit, atomicity might be compromised.
        # Consider refactoring upsert_data later.
        logger.info(f"Successfully processed order {platform}/{order_id} and its items.")

    except SQLAlchemyError as e:
        logger.error(f"Database error during upsert_order_with_items for order {platform}/{order_id}: {e}", exc_info=True)
        # Rollback might be handled by the caller's finally block
        # db.rollback()
        raise # Re-raise the exception to notify the caller
    except Exception as e:
        logger.error(f"Unexpected error during upsert_order_with_items for order {platform}/{order_id}: {e}", exc_info=True)
        # db.rollback()
        raise
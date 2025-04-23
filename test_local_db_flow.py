# test_local_db_flow.py
import datetime
from decimal import Decimal

# 确保在运行此脚本前，相关模块可以被正确导入
# 可能需要调整 Python 路径或确保在项目根目录运行
from core.db import db_session
from core.models import Order, OrderItem, User, Product, SyncStatus
from core.loaders import upsert_data
from utils.logger import logger
from config.config import settings # 确保配置已加载

def run_local_db_test():
    logger.info("Starting local database flow test...")

    # 准备一些样本数据 (键名与模型列名对齐)
    sample_user_data = [
        {'platform': 'xiaoe', 'user_id': 'test_user_001', 'nickname': '测试用户1', 'phone': '13800000001', 'register_time': datetime.datetime.now()},
        {'platform': 'xiaoe', 'user_id': 'test_user_002', 'nickname': '测试用户2', 'phone': '13900000002', 'register_time': datetime.datetime.now() - datetime.timedelta(days=1)},
    ]

    sample_product_data = [
        {'platform': 'xiaoe', 'product_id': 'test_prod_A', 'type': 1, 'name': '测试商品A', 'price_low': Decimal('99.99'), 'price_high': Decimal('99.99'), 'status': 1}, # title -> name, price -> price_low/high, product_type -> type
        {'platform': 'xiaoe', 'product_id': 'test_prod_B', 'type': 2, 'name': '测试商品B', 'price_low': Decimal('19.80'), 'price_high': Decimal('19.80'), 'status': 1}, # title -> name, price -> price_low/high, product_type -> type
    ]

    sample_order_data = [
        {
            'platform': 'xiaoe',
            'order_id': 'test_order_1001',
            'user_id': 'test_user_001',
            'goods_original_total_price': Decimal('99.99'), # total_price -> goods_original_total_price (或其他合适的价格字段)
            'actual_fee': Decimal('99.99'),            # pay_price -> actual_fee (或其他合适的价格字段)
            'order_state': 1,
            'pay_state_time': datetime.datetime.now() - datetime.timedelta(minutes=30), # pay_time -> pay_state_time
            'created_at_platform': datetime.datetime.now() - datetime.timedelta(minutes=35), # created_at -> created_at_platform
            'update_time_platform': datetime.datetime.now() - datetime.timedelta(minutes=30), # updated_at -> update_time_platform (或其他合适的更新时间字段)
        }
    ]

    sample_order_item_data = [
        {
            'platform': 'xiaoe',
            'order_id': 'test_order_1001',
            'item_id': 'item_1001_A',
            'product_id': 'test_prod_A',
            'resource_type': 1,       # product_type -> resource_type (或其他合适的类型字段)
            'quantity': 1,
            'unit_price': Decimal('99.99'), # price -> unit_price (或其他合适的价格字段)
            'total_price': Decimal('99.99'),
        }
    ]

    # 修正 sample_sync_status_data 以匹配 SyncStatus 模型定义
    sample_sync_status_data = [
        {
            'sync_target': 'xiaoe_orders_test', # 提供主键值
            'last_sync_time': datetime.datetime.now() - datetime.timedelta(days=1), # 提供一个值
            # last_sync_id, sync_cursor, run times 是 nullable，可以不提供初始值
            'status': 'success', # 提供一个状态值
            'message': 'Initial test record' # 提供一个消息
        }
    ]


    logger.info("Attempting to connect to database and get session...")
    # 使用数据库会话
    with db_session() as session:
        logger.info("Database session obtained.")

        # (可选) 在测试前清空表数据，避免重复记录干扰
        try:
            logger.warning("Clearing test tables before inserting new data...")
            # 按依赖关系反向删除
            session.query(OrderItem).delete()
            session.query(Order).delete()
            session.query(Product).delete()
            session.query(User).delete()
            session.query(SyncStatus).delete()
            session.commit()
            logger.info("Test tables cleared.")
        except Exception as e:
            logger.error(f"Error clearing tables: {e}", exc_info=True)
            session.rollback()
            # 清理失败可能不影响插入，但最好记录下来
            pass # 继续执行插入


        try:
            # 使用 upsert_data 加载数据

            # 加载用户数据
            logger.info(f"Upserting {len(sample_user_data)} user records...")
            upsert_data(session, User, sample_user_data)
            logger.info("User data upserted.")

            # 加载商品数据
            logger.info(f"Upserting {len(sample_product_data)} product records...")
            upsert_data(session, Product, sample_product_data)
            logger.info("Product data upserted.")

            # 加载订单数据
            logger.info(f"Upserting {len(sample_order_data)} order records...")
            upsert_data(session, Order, sample_order_data)
            logger.info("Order data upserted.")

            # 加载订单项数据
            logger.info(f"Upserting {len(sample_order_item_data)} order item records...")
            upsert_data(session, OrderItem, sample_order_item_data)
            logger.info("Order item data upserted.")

             # 加载同步状态数据
            logger.info(f"Upserting {len(sample_sync_status_data)} sync status records...")
            upsert_data(session, SyncStatus, sample_sync_status_data)
            logger.info("Sync status data upserted.")

            # 注意：由于 upsert_data 内部会 commit，这里不再需要 session.commit()
            # session.commit()
            logger.info("Data successfully upserted (committed within upsert_data) to the local database.")

        except Exception as e:
            logger.error(f"An error occurred during database operation: {e}", exc_info=True)
            # session.rollback() # upsert_data 内部已处理回滚
            logger.warning("Transaction rolled back (handled within upsert_data).")
        # finally:
            # db_session.remove() # 使用 with db_session() 时，通常不需要手动 remove

    logger.info("Local database flow test finished.")

if __name__ == "__main__":
    # 导入并调用日志配置函数
    from utils.logger import setup_logging
    setup_logging()

    # 现在 logger 已经配置好了，可以运行测试
    run_local_db_test() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小鹅通数据同步主脚本

负责根据命令行参数触发不同类型的同步任务。
"""

import argparse
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

# 确保项目根目录在 sys.path 中，以便导入模块
# (这在使用绝对路径的 cron 任务或直接运行时很有用)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 现在可以安全地导入项目模块了
from config.config import settings
from utils.logger import logger, setup_logging
from core.db import get_db, SessionLocal, engine, Base
from core.models import Order, OrderItem, User, Product, SyncStatus, AftersaleOrder, AftersaleItem
from core.loaders import upsert_data, upsert_aftersale_orders_with_user_lookup, replace_aftersale_items, upsert_order_with_items
from platforms.xiaoe.client import XiaoeClient, XiaoeAuthError, XiaoeRequestError
from platforms.xiaoe.transformers import (
    transform_order, transform_order_items, transform_user, transform_product, 
    transform_after_sale_order, transform_aftersale_items,
    transform_order_details_data
)
import time # 导入 time 模块

# --- 同步函数定义 --- 

def update_sync_status(db: Session, sync_target: str, 
                       status: str, message: Optional[str] = None, 
                       start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, 
                       last_sync_ts: Optional[datetime] = None):
    """更新同步状态表，使用 sync_target 作为主键。"""
    try:
        # 尝试查找现有记录
        sync_record = db.query(SyncStatus).filter_by(sync_target=sync_target).first()

        if not sync_record:
            sync_record = SyncStatus(sync_target=sync_target)
            db.add(sync_record)
        
        sync_record.status = status
        sync_record.message = message
        # Map start_time/end_time to model fields
        sync_record.last_successful_run_start = start_time 
        sync_record.last_successful_run_end = end_time
        if last_sync_ts is not None: # 允许设置为 None
            # Map last_sync_ts to the correct model field
            sync_record.last_sync_time = last_sync_ts
        
        db.commit()
        logger.info(f"Sync status updated for {sync_target}: {status}")
    except Exception as e:
        logger.error(f"Failed to update sync status for {sync_target}: {e}", exc_info=True)
        db.rollback()

def get_last_sync_timestamp(db: Session, sync_target: str) -> Optional[datetime]:
    """获取上次成功同步的时间戳，使用 sync_target 作为主键。"""
    try:
        # Use sync_target for filtering and last_sync_time for the timestamp
        sync_record = db.query(SyncStatus).filter_by(
            sync_target=sync_target, status='success'
        ).order_by(SyncStatus.last_sync_time.desc()).first()
        
        if sync_record and sync_record.last_sync_time:
            ts = sync_record.last_sync_time
            # 确保返回的是带 UTC 时区信息的 datetime 对象
            if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
                 ts = ts.replace(tzinfo=timezone.utc)
            else:
                 ts = ts.astimezone(timezone.utc) # 转换为UTC
            logger.info(f"Retrieved last sync timestamp for {sync_target}: {ts.isoformat()}")
            return ts
        else:
            logger.info(f"No previous successful sync timestamp found for {sync_target}. Will sync from beginning or default.")
            return None
    except Exception as e:
        logger.error(f"Failed to get last sync timestamp for {sync_target}: {e}", exc_info=True)
        return None

def run_incremental_sync():
    """执行小鹅通订单的增量同步。"""
    # Define a specific sync_target for this task
    sync_target = "xiaoe_order_incremental"
    logger.info(f"Starting {sync_target} sync...")
    start_run_time = datetime.now(timezone.utc)
    db = SessionLocal() # 获取新的 session
    sync_status = "failed" # 默认失败
    error_message = None
    last_sync_ts = None # 初始化
    new_last_sync_ts = start_run_time # 默认将本次开始时间作为下次同步起点
    processed_order_count = 0
    failed_order_count = 0

    try:
        # 1. 获取上次同步时间戳 using sync_target
        last_sync_ts = get_last_sync_timestamp(db, sync_target)
        if last_sync_ts is None:
            # TODO: 从配置或固定值读取初始同步时间
            # 暂定为1天前
            start_sync_dt = start_run_time - timedelta(days=1)
            logger.warning(f"No last sync timestamp found for {sync_target}. Starting sync from {start_sync_dt.isoformat()}")
        else:
            start_sync_dt = last_sync_ts
            new_last_sync_ts = last_sync_ts # 默认保留上次的时间戳，除非成功获取到新数据

        # 结束时间用运行开始时间，避免遗漏运行期间产生的数据
        end_sync_dt = start_run_time

        # 转换为 API 需要的字符串格式 (YYYY-MM-DD HH:MM:SS)
        start_time_str = (start_sync_dt + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_sync_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # 2. 初始化 API Client
        client = XiaoeClient()
        
        # 3. 分页获取订单数据 (只获取ID列表，然后逐个获取详情)
        page_index = 1 # Use page_index as per client method
        page_size = 50 # 每次请求获取的数量
        # Removed all_orders and all_order_items lists
        total_orders_fetched_list = 0
        # latest_order_created_at = None # Using run start time is safer for timestamp update
        
        # Use the generator returned by get_orders
        for page_response_data in client.get_orders(page_size=page_size, start_time=start_time_str, end_time=end_time_str, order_state=2):
            # No need to manage page_index manually, client handles it.
            
            orders_in_page = page_response_data.get('list', [])
            total_count_in_page = len(orders_in_page)
            total_orders_fetched_list += total_count_in_page
            logger.info(f"Processing {total_count_in_page} orders from list API page. Total listed so far: {total_orders_fetched_list}")

            if not orders_in_page:
                # Should not happen if client generator works correctly, but good practice
                logger.info("No orders found in this page response from generator.")
                continue # Continue to next iteration (though likely loop ends)
                
            # 4. 获取详情并处理每个订单
            for order_summary in orders_in_page:
                order_id = None
                try:
                    # Extract order_id carefully
                    order_info = order_summary.get('order_info', {})
                    order_id = order_info.get('order_id')
                    if not order_id:
                        logger.warning(f"Skipping order summary due to missing order_id: {order_summary}")
                        failed_order_count += 1
                        continue

                    # Fetch details for this specific order
                    logger.debug(f"Fetching details for order_id: {order_id}")
                    detail_response_data = client.get_order_details(order_id)

                    # Transform the detailed data
                    transformed_detail = transform_order_details_data(detail_response_data)

                    if transformed_detail:
                        # Upsert order and items using the combined loader function
                        upsert_order_with_items(db, transformed_detail['order'], transformed_detail['order_items'])
                        logger.info(f"Successfully processed and upserted order {order_id}.")
                        processed_order_count += 1
                        # Update the timestamp if we successfully process any order
                        new_last_sync_ts = end_sync_dt
                    else:
                        logger.warning(f"Transformation failed for order details {order_id}. Skipping upsert.")
                        failed_order_count += 1
                        # Potentially store failed order IDs for later inspection/retry

                except (XiaoeAuthError, XiaoeRequestError) as api_detail_error:
                    # Error fetching or processing *details* for a specific order
                    logger.error(f"API error processing details for order {order_id}: {api_detail_error}. Skipping this order.", exc_info=False) # exc_info=False to avoid flooding logs
                    failed_order_count += 1
                    # Continue to the next order in the page
                    continue 
                except Exception as process_error:
                    # Unexpected error during detail fetch, transform, or upsert
                    logger.error(f"Unexpected error processing order {order_id}: {process_error}. Skipping this order.", exc_info=True)
                    failed_order_count += 1
                    # Continue to the next order
                    continue
            
            # No need for explicit page increment or break logic, generator handles it.
            # Optional: Add a small delay between processing pages if needed, though client might handle it
            time.sleep(0.2) # Small delay after processing a page

        # 5. 移除旧的批量加载逻辑
        # No need for bulk upsert here, done individually above

        # --- Commit transaction before updating status if successful ---
        db.commit() 
        logger.info(f"Main data transaction committed for {sync_target}.")
        # --------------------------------------------------------------

        # 6. 如果成功处理了任何订单，设置状态为 success
        if processed_order_count > 0:
            sync_status = "success"
            error_message = None # Clear previous errors if at least one succeeded
            if failed_order_count > 0:
                 sync_status = "partial_success" # Indicate some failures occurred
                 error_message = f"{failed_order_count} orders failed during detail processing."
            logger.info(f"Xiaoe incremental order sync finished. Processed: {processed_order_count}, Failed: {failed_order_count}.")
        elif failed_order_count > 0:
             sync_status = "failed"
             error_message = f"All ({failed_order_count}) attempts failed during detail processing."
             logger.error(f"Xiaoe incremental order sync failed. {error_message}")
             new_last_sync_ts = last_sync_ts # Revert timestamp on complete failure
        else:
             # No orders fetched or processed, could be success if the time range was empty
             sync_status = "success"
             error_message = "No new orders found in the specified time range."
             logger.info(error_message)
             # Keep the new_last_sync_ts as end_sync_dt even if no orders found

    except (XiaoeAuthError, XiaoeRequestError) as api_list_error:
        # Error fetching the *list* of orders
        sync_status = "failed"
        error_message = f"API error fetching order list: {api_list_error}"
        logger.error(f"Xiaoe incremental order sync failed: {error_message}", exc_info=True)
        new_last_sync_ts = last_sync_ts # Revert timestamp on list failure

    except Exception as e:
        sync_status = "failed"
        if not error_message: # General error outside the detail loop
            error_message = f"Unexpected error during incremental sync: {e}"
        logger.error(f"Xiaoe incremental order sync failed: {error_message}", exc_info=True)
        # 失败时不更新 new_last_sync_ts，保留上一次成功的时间戳
        new_last_sync_ts = last_sync_ts

    finally:
        # 7. 更新同步状态表 using sync_target
        end_run_time = datetime.now(timezone.utc)
        update_sync_status(db, sync_target, # Pass sync_target instead of platform/data_type/mode
                           sync_status, error_message, 
                           start_run_time, end_run_time, 
                           new_last_sync_ts)
        db.close() # 关闭 session
        logger.info(f"Database session closed for {sync_target}. Processed: {processed_order_count}, Failed: {failed_order_count}")

def run_status_update_sync():
    """执行小鹅通近期订单的状态更新。"""
    # Define a specific sync_target for this task
    sync_target = "xiaoe_order_status_update"
    logger.info(f"Starting {sync_target} sync...")
    start_run_time = datetime.now(timezone.utc)
    db = SessionLocal()
    sync_status = "failed"
    error_message = None
    processed_order_count = 0
    failed_order_count = 0

    try:
        # 1. 确定要检查的时间范围 (基于订单 *创建* 时间)
        update_days = settings.STATUS_UPDATE_DAYS
        start_scan_dt = start_run_time - timedelta(days=update_days)
        end_scan_dt = start_run_time # 扫描到当前

        start_time_str = start_scan_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_scan_dt.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Scanning orders CREATED from {start_time_str} to {end_time_str} for status update.")

        # 2. 初始化 API Client
        client = XiaoeClient()

        # 3. 分页获取近期创建的订单列表 (仅获取 ID)
        page_size = 50 # 或从配置读取
        total_orders_fetched_list = 0
        # Removed all_orders_to_update and all_items_to_update lists

        # Use the generator returned by get_orders
        for page_response_data in client.get_orders(
            page_size=page_size, 
            start_time=start_time_str, 
            end_time=end_time_str,
            # Don't filter by order_state, we want to update any recent order regardless of initial state
        ):
            orders_in_page = page_response_data.get('list', [])
            total_count_in_page = len(orders_in_page)
            total_orders_fetched_list += total_count_in_page
            logger.info(f"Processing {total_count_in_page} recent orders from list API page. Total listed so far: {total_orders_fetched_list}")

            if not orders_in_page:
                continue

            # 4. 获取详情并处理每个订单
            for order_summary in orders_in_page:
                order_id = None
                try:
                    order_info = order_summary.get('order_info', {})
                    order_id = order_info.get('order_id')
                    if not order_id:
                        logger.warning(f"Skipping order summary in status update due to missing order_id: {order_summary}")
                        failed_order_count += 1
                        continue

                    # Fetch details for this specific order
                    logger.debug(f"Fetching details for order {order_id} (status update)...")
                    detail_response_data = client.get_order_details(order_id)

                    # Transform the detailed data
                    transformed_detail = transform_order_details_data(detail_response_data)

                    if transformed_detail:
                        # Upsert using the combined loader function
                        upsert_order_with_items(db, transformed_detail['order'], transformed_detail['order_items'])
                        logger.info(f"Successfully checked and updated order {order_id} (status update).")
                        processed_order_count += 1
                    else:
                        logger.warning(f"Transformation failed for order details {order_id} during status update. Skipping upsert.")
                        failed_order_count += 1

                except (XiaoeAuthError, XiaoeRequestError) as api_detail_error:
                    logger.error(f"API error processing details for order {order_id} during status update: {api_detail_error}. Skipping.", exc_info=False)
                    failed_order_count += 1
                    continue
                except Exception as process_error:
                    logger.error(f"Unexpected error processing order {order_id} during status update: {process_error}. Skipping.", exc_info=True)
                    failed_order_count += 1
                    continue
            
            # No need for explicit page increment or break logic, generator handles it.
            # Optional: Add a small delay between processing pages if needed, though client might handle it
            time.sleep(0.2) # Small delay after processing a page

        # 5. 移除旧的批量加载逻辑
        # Bulk upsert removed, handled individually above

        # --- Commit transaction before updating status if successful ---
        db.commit() 
        logger.info(f"Main data transaction committed for {sync_target}.")
        # --------------------------------------------------------------

        # 6. 更新状态
        if processed_order_count > 0:
            sync_status = "success"
            error_message = None
            if failed_order_count > 0:
                 sync_status = "partial_success"
                 error_message = f"{failed_order_count} orders failed during status update processing."
            logger.info(f"Xiaoe status update sync finished. Processed: {processed_order_count}, Failed: {failed_order_count}.")
        elif failed_order_count > 0:
             sync_status = "failed"
             error_message = f"All ({failed_order_count}) attempts failed during status update processing."
             logger.error(f"Xiaoe status update sync failed. {error_message}")
        else:
             sync_status = "success"
             error_message = "No recent orders found or processed in the specified time range for status update."
             logger.info(error_message)

    except (XiaoeAuthError, XiaoeRequestError) as api_list_error:
        # Error fetching the *list* of orders
        sync_status = "failed"
        error_message = f"API error fetching order list for status update: {api_list_error}"
        logger.error(f"Xiaoe status update sync failed: {error_message}", exc_info=True)

    except Exception as e:
        sync_status = "failed"
        if not error_message:
            error_message = f"Unexpected error during status update sync: {e}"
        logger.error(f"Xiaoe status update sync failed: {error_message}", exc_info=True)
    
    finally:
        # 7. 更新同步状态表 using sync_target
        end_run_time = datetime.now(timezone.utc)
        # Status update task doesn't update last_sync_timestamp (last_sync_time)
        update_sync_status(db, sync_target, # Pass sync_target
                           sync_status, error_message, 
                           start_run_time, end_run_time, 
                           None) # Pass None for last_sync_ts
        db.close()
        logger.info(f"Database session closed for {sync_target}. Processed: {processed_order_count}, Failed: {failed_order_count}")

def run_after_sale_sync(full_sync: bool = False):
    """执行小鹅通售后订单的同步（全量或增量）。"""
    # Define sync_targets based on full_sync flag
    mode = "full" if full_sync else "incremental"
    sync_target = f"xiaoe_aftersale_{mode}"
    logger.info(f"Starting {sync_target} sync...")
    start_run_time = datetime.now(timezone.utc)
    db = SessionLocal()
    sync_status = "failed" 
    error_message = None
    last_sync_ts = None
    new_last_sync_ts = start_run_time 

    try:
        client = XiaoeClient()
        all_aftersale_orders = []
        all_aftersale_items = []
        total_fetched = 0
        page = 1
        page_size = 50

        # 确定查询时间范围
        start_sync_dt = None
        end_sync_dt = start_run_time # 结束时间总是当前运行时间

        if not full_sync:
            last_sync_ts = get_last_sync_timestamp(db, sync_target)
            if last_sync_ts:
                start_sync_dt = last_sync_ts
                new_last_sync_ts = last_sync_ts # 默认保留上次时间戳
            else:
                # 首次增量，从配置或默认时间开始（例如1天前）
                start_sync_dt = start_run_time - timedelta(days=settings.INITIAL_SYNC_DAYS)
                logger.warning(f"No last sync timestamp for incremental aftersale sync. Starting from {start_sync_dt.isoformat()}")
        else:
            # 全量同步，不限制开始时间 (API 可能需要一个非常早的时间或不支持为空)
            # 需要查阅 get_aftersales API 是否支持不传 start_time
            # 假设传 None 或非常早的时间表示全量
            start_sync_dt = None 
            logger.info("Performing a full sync of aftersale orders.")

        # 时间格式化 (如果需要)
        start_time_str = (start_sync_dt + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S") if start_sync_dt else None
        end_time_str = end_sync_dt.strftime("%Y-%m-%d %H:%M:%S")

        while True:
            logger.info(f"Fetching page {page} for {sync_target} (size={page_size}) from {start_time_str or 'beginning'} to {end_time_str}")
            try:
                # 调用 API 获取数据 (需要确认API参数, 假设与订单类似)
                # 假设 get_aftersales 支持 start_time, end_time, page, page_size
                # 修正方法名为 get_after_sale_orders，并显式添加 date_type
                response_data = client.get_after_sale_orders(
                    page=page, 
                    page_size=page_size, 
                    start_time=start_time_str, 
                    end_time=end_time_str,
                    date_type='created_at' # 显式指定按创建时间查询
                )

                aftersales_in_page = response_data.get('list', [])
                if not aftersales_in_page:
                    logger.info("No more aftersale orders found in this page/range.")
                    break

                total_fetched += len(aftersales_in_page)
                logger.info(f"Fetched {len(aftersales_in_page)} aftersale orders on page {page}. Total fetched so far: {total_fetched}")

                # 转换数据
                for raw_aftersale in aftersales_in_page:
                    transformed_order = transform_after_sale_order(raw_aftersale)
                    if transformed_order:
                        all_aftersale_orders.append(transformed_order)
                        # 同时提取售后商品项
                        transformed_items = transform_aftersale_items(raw_aftersale)
                        if transformed_items:
                            all_aftersale_items.extend(transformed_items)
                
                # 分页逻辑 (假设与订单类似)
                if len(aftersales_in_page) < page_size:
                    logger.info("Fetched less aftersale orders than page size, assuming last page.")
                    break
                
                page += 1
                if page > 500: # Max page limit
                    logger.warning("Reached maximum page limit (500). Stopping fetch.")
                    break
                time.sleep(0.5) # API rate limit

            except (XiaoeAuthError, XiaoeRequestError) as api_error:
                error_message = f"API error fetching aftersale page {page}: {api_error}"
                logger.error(error_message, exc_info=True)
                raise 
            except Exception as fetch_error:
                error_message = f"Unexpected error fetching aftersale page {page}: {fetch_error}"
                logger.error(error_message, exc_info=True)
                raise

        # 加载数据到数据库
        if all_aftersale_orders:
            logger.info(f"Upserting {len(all_aftersale_orders)} transformed aftersale orders...")
            upsert_aftersale_orders_with_user_lookup(db, all_aftersale_orders)
        else:
            logger.info("No new valid aftersale orders to process.")

        if all_aftersale_items:
            logger.info(f"Replacing {len(all_aftersale_items)} transformed aftersale items...")
            replace_aftersale_items(db, all_aftersale_items)
        else:
            logger.info("No new valid aftersale items to process.")

        # --- Commit transaction before updating status if successful ---
        db.commit()
        logger.info(f"Main data transaction committed for {sync_target}.")
        # --------------------------------------------------------------

        # 如果成功，设置状态并更新时间戳 (仅增量模式)
        sync_status = "success"
        if not full_sync:
            new_last_sync_ts = end_sync_dt # 增量同步，下次从本次运行开始时间起
        # 对于全量，new_last_sync_ts 保留为 start_run_time 或 None
        logger.info(f"Xiaoe aftersale order sync (mode: {mode}) completed successfully.")

    except Exception as e:
        sync_status = "failed"
        if not error_message:
            error_message = f"Error during aftersale data processing or loading: {e}"
        logger.error(f"Xiaoe aftersale order sync (mode: {mode}) failed: {error_message}", exc_info=True)
        # 失败时，增量模式保留上次时间戳
        if not full_sync:
            new_last_sync_ts = last_sync_ts
        else:
            new_last_sync_ts = None # 全量失败，下次还是全量

    finally:
        # 更新同步状态表 using sync_target
        end_run_time = datetime.now(timezone.utc)
        update_sync_status(db, sync_target, # Pass sync_target
                           sync_status, error_message, 
                           start_run_time, end_run_time, 
                           new_last_sync_ts if not full_sync else None) # Update timestamp only for incremental
        db.close()
        logger.info(f"Database session closed for {sync_target}.")

# --- 主程序入口 ---
def main():
    # Setup logging first!
    setup_logging()

    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="Run Xiaoe data synchronization tasks.")
    parser.add_argument(
        "--sync-type", 
        type=str, 
        choices=["incremental", "status_update", "full_order", "aftersales"], # 添加 'aftersales'
        required=True,
        help="Type of sync to perform: \n"
             "  incremental: Sync new orders since last successful run.\n"
             "  status_update: Check and update status for recent orders.\n"
             "  full_order: Perform a full sync of all orders (use with caution!).\n"
             "  aftersales: Sync aftersale orders (use --full for initial sync)."
    )
    # 添加 --full 标志，主要用于 aftersales 和 full_order
    parser.add_argument(
        "--full",
        action="store_true",
        help="Perform a full sync instead of incremental (applies to 'aftersales' and 'full_order')."
    )
    # 可以添加其他参数，如日期范围等
    # parser.add_argument("--start-date", type=str, help="Start date for full sync (YYYY-MM-DD).")
    # parser.add_argument("--end-date", type=str, help="End date for full sync (YYYY-MM-DD).")

    args = parser.parse_args()

    # 2. 根据参数执行相应的同步函数
    logger.info(f"Executing sync task with arguments: {args}")

    if args.sync_type == "incremental":
        run_incremental_sync()
    elif args.sync_type == "status_update":
        run_status_update_sync()
    elif args.sync_type == "full_order":
        # TODO: 实现全量订单同步逻辑 (run_full_order_sync)
        logger.warning("Full order sync (run_full_order_sync) is not yet implemented.")
        # run_full_order_sync(start_date=args.start_date, end_date=args.end_date)
        pass
    elif args.sync_type == "aftersales":
        run_after_sale_sync(full_sync=args.full)
    else:
        logger.error(f"Unknown sync type: {args.sync_type}")
        sys.exit(1)

    logger.info("Sync task finished.")

if __name__ == "__main__":
    # 可以在这里添加表创建逻辑 (可选, 最好独立)
    # try:
    #     logger.info("Checking/Creating database tables...")
    #     Base.metadata.create_all(bind=engine) 
    #     logger.info("Tables checked/created.")
    # except Exception as table_error:
    #     logger.critical(f"Failed to check/create tables: {table_error}", exc_info=True)
    #     sys.exit(1)
        
    main() 
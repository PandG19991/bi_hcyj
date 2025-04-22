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
from core.loaders import upsert_data, upsert_aftersale_orders_with_user_lookup, replace_aftersale_items
from platforms.xiaoe.client import XiaoeClient, XiaoeAuthError, XiaoeRequestError
from platforms.xiaoe.transformers import (
    transform_order, transform_order_items, transform_user, transform_product, 
    transform_after_sale_order, transform_aftersale_items
)
import time # 导入 time 模块

# --- 同步函数定义 --- 

def update_sync_status(db: Session, platform: str, data_type: str, mode: str, 
                       status: str, message: Optional[str] = None, 
                       start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, 
                       last_sync_ts: Optional[datetime] = None):
    """更新同步状态表。"""
    try:
        # 尝试查找现有记录
        sync_record = db.query(SyncStatus).filter_by(
            platform=platform, data_type=data_type, sync_mode=mode
        ).first()

        if not sync_record:
            sync_record = SyncStatus(
                platform=platform,
                data_type=data_type,
                sync_mode=mode
            )
            db.add(sync_record)
        
        sync_record.status = status
        sync_record.message = message
        sync_record.last_run_start_time = start_time
        sync_record.last_run_end_time = end_time
        if last_sync_ts is not None: # 允许设置为 None
            sync_record.last_sync_timestamp = last_sync_ts
        
        db.commit()
        logger.info(f"Sync status updated for {platform}/{data_type}/{mode}: {status}")
    except Exception as e:
        logger.error(f"Failed to update sync status for {platform}/{data_type}/{mode}: {e}", exc_info=True)
        db.rollback()

def get_last_sync_timestamp(db: Session, platform: str, data_type: str, mode: str) -> Optional[datetime]:
    """获取上次成功同步的时间戳。"""
    try:
        sync_record = db.query(SyncStatus).filter_by(
            platform=platform, data_type=data_type, sync_mode=mode, status='success'
        ).order_by(SyncStatus.last_sync_timestamp.desc()).first()
        
        if sync_record and sync_record.last_sync_timestamp:
            ts = sync_record.last_sync_timestamp
            # 确保返回的是带 UTC 时区信息的 datetime 对象
            if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
                 # 假设数据库存储的是naive datetime, 且代表UTC时间
                 ts = ts.replace(tzinfo=timezone.utc)
            else:
                 ts = ts.astimezone(timezone.utc) # 转换为UTC
            logger.info(f"Retrieved last sync timestamp for {platform}/{data_type}/{mode}: {ts.isoformat()}")
            return ts
        else:
            logger.info(f"No previous successful sync timestamp found for {platform}/{data_type}/{mode}. Will sync from beginning or default.")
            return None
    except Exception as e:
        logger.error(f"Failed to get last sync timestamp for {platform}/{data_type}/{mode}: {e}", exc_info=True)
        return None

def run_incremental_sync():
    """执行小鹅通订单的增量同步。"""
    logger.info("Starting Xiaoe incremental order sync...")
    start_run_time = datetime.now(timezone.utc)
    platform = "xiaoe"
    data_type = "order"
    mode = "incremental"
    db = SessionLocal() # 获取新的 session
    sync_status = "failed" # 默认失败
    error_message = None
    last_sync_ts = None # 初始化
    new_last_sync_ts = start_run_time # 默认将本次开始时间作为下次同步起点

    try:
        # 1. 获取上次同步时间戳
        last_sync_ts = get_last_sync_timestamp(db, platform, data_type, mode)
        if last_sync_ts is None:
            # TODO: 从配置或固定值读取初始同步时间
            # 暂定为1天前
            start_sync_dt = start_run_time - timedelta(days=1)
            logger.warning(f"No last sync timestamp found. Starting sync from {start_sync_dt.isoformat()}")
        else:
            start_sync_dt = last_sync_ts
            new_last_sync_ts = last_sync_ts # 默认保留上次的时间戳，除非成功获取到新数据

        # 结束时间用运行开始时间，避免遗漏运行期间产生的数据
        end_sync_dt = start_run_time

        # 转换为 API 需要的字符串格式 (YYYY-MM-DD HH:MM:SS)
        # 加一点点缓冲，避免精度问题导致重复获取边界数据
        start_time_str = (start_sync_dt + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_sync_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # 2. 初始化 API Client
        client = XiaoeClient()
        
        # 3. 分页获取订单数据
        page = 1
        page_size = 50 # 每次请求获取的数量
        all_orders = []
        all_order_items = []
        total_orders_fetched = 0
        latest_order_created_at = None # 记录本次同步到的最新订单时间
        
        while True:
            # logger.info(f"Fetching page {page} of orders (state=2, size={page_size}) from {start_time_str} to {end_time_str}")
            try:
                # 恢复使用 order_state=2 获取支付成功的订单 (根据文档 1.0.2)
                logger.info(f"Fetching page {page} of PAID orders (state=2, size={page_size}) from {start_time_str} to {end_time_str}")
                response_data = client.get_orders(page=page, page_size=page_size, start_time=start_time_str, end_time=end_time_str, order_state=2)
                # 移除之前的临时代码
                # logger.info(f"Temporarily fetching ALL order states for page {page} to bypass API error 40004.")
                # response_data = client.get_orders(page=page, page_size=page_size, start_time=start_time_str, end_time=end_time_str)

                orders_in_page = response_data.get('list', [])
                # API可能不返回total_count，或者不准确，依赖 list 是否为空
                # total_count = response_data.get('total_count', 0)
                
                if not orders_in_page:
                    logger.info("No more orders found in this page/range.")
                    break
                    
                total_orders_fetched += len(orders_in_page)
                logger.info(f"Fetched {len(orders_in_page)} orders on page {page}. Total fetched so far: {total_orders_fetched}")
                
                # 4. 转换数据
                for order_raw in orders_in_page:
                    order_transformed = transform_order(order_raw)
                    if order_transformed:
                        all_orders.append(order_transformed)
                        # 同时提取订单项
                        items_transformed = transform_order_items(order_raw)
                        if items_transformed:
                            all_order_items.extend(items_transformed)
                        # 更新本次同步到的最新订单创建时间
                        if order_transformed.get('created_at'):
                            current_order_dt = order_transformed['created_at']
                            if latest_order_created_at is None or current_order_dt > latest_order_created_at:
                                latest_order_created_at = current_order_dt
                
                # 判断是否需要继续获取下一页 (小鹅通常规分页逻辑)
                # 如果返回的列表数量小于请求的page_size，说明是最后一页了
                if len(orders_in_page) < page_size:
                    logger.info("Fetched less orders than page size, assuming last page.")
                    break
                
                page += 1
                if page > 500: # Max page limit
                    logger.warning("Reached maximum page limit (500). Stopping fetch.")
                    break
                time.sleep(0.5) # API rate limit
                
            except (XiaoeAuthError, XiaoeRequestError) as api_error:
                error_message = f"API error fetching page {page}: {api_error}"
                logger.error(error_message, exc_info=True)
                raise # 重新抛出，让外层 try 处理状态更新
            except Exception as fetch_error:
                error_message = f"Unexpected error fetching page {page}: {fetch_error}"
                logger.error(error_message, exc_info=True)
                raise
                
        # 5. 加载数据到数据库
        if all_orders:
            logger.info(f"Upserting {len(all_orders)} transformed orders...")
            upsert_data(db, Order, all_orders)
        else:
            logger.info("No new valid orders to upsert.")
            
        if all_order_items:
            logger.info(f"Upserting {len(all_order_items)} transformed order items...")
            # 假设 upsert_data 可以处理 OrderItem (基于唯一键 uk_order_product)
            # 如果 loaders.py 中的 upsert 未针对此唯一键优化，这里可能效率不高或行为不符合预期
            # 需要确认 loaders.py 的实现是否处理了这种情况
            # 临时策略：MVP阶段，我们相信增量只带来新数据，直接UPSERT
            upsert_data(db, OrderItem, all_order_items)
        else:
            logger.info("No new valid order items to upsert.")

        # 6. 如果成功，设置状态为 success
        sync_status = "success"
        # 更新时间戳：用本次运行开始时间作为下次起点，确保不会遗漏
        new_last_sync_ts = end_sync_dt
        # 或者，用本次获取到的最新订单时间作为下次起点 (需要API保证顺序)
        # if latest_order_created_at:
        #     new_last_sync_ts = latest_order_created_at
        logger.info("Xiaoe incremental order sync completed successfully.")

    except Exception as e:
        sync_status = "failed"
        if not error_message: # 如果错误发生在 upsert 阶段
            error_message = f"Error during data processing or upsert: {e}"
        logger.error(f"Xiaoe incremental order sync failed: {error_message}", exc_info=True)
        # 失败时不更新 new_last_sync_ts，保留上一次成功的时间戳
        new_last_sync_ts = last_sync_ts

    finally:
        # 7. 更新同步状态表
        end_run_time = datetime.now(timezone.utc)
        update_sync_status(db, platform, data_type, mode, 
                           sync_status, error_message, 
                           start_run_time, end_run_time, 
                           new_last_sync_ts)
        db.close() # 关闭 session
        logger.info("Database session closed for incremental sync.")

def run_status_update_sync():
    """执行小鹅通近期订单的状态更新。"""
    logger.info("Starting Xiaoe order status update sync...")
    start_run_time = datetime.now(timezone.utc)
    platform = "xiaoe"
    data_type = "order"
    mode = "status_update"
    sync_target = "xiaoe_orders_status_update"
    db = SessionLocal()
    sync_status = "failed"
    error_message = None

    try:
        # 1. 确定要检查的时间范围
        update_days = settings.STATUS_UPDATE_DAYS
        start_scan_dt = start_run_time - timedelta(days=update_days)
        end_scan_dt = start_run_time # 扫描到当前

        start_time_str = start_scan_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_scan_dt.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Fetching orders created from {start_time_str} to {end_time_str} for status update.")

        # 2. 初始化 API Client
        client = XiaoeClient()

        # 3. 分页获取近期创建的订单 (不再基于数据库查询的 ID 列表)
        page = 1
        page_size = 50 # 或从配置读取
        all_orders_to_update = []
        all_items_to_update = [] # 同时处理订单项
        total_orders_fetched = 0
        
        while True:
            logger.info(f"Fetching page {page} of recent orders (size={page_size}) for status update...")
            try:
                # 调用 get_orders 获取该时间段内创建的所有状态的订单
                # 注意：API 按创建时间筛选，但 UPSERT 会更新找到的订单
                response_data = client.get_orders(
                    page=page, 
                    page_size=page_size, 
                    start_time=start_time_str, 
                    end_time=end_time_str
                    # 不指定 order_state 以获取所有状态
                )
                
                orders_in_page = response_data.get('list', [])
                # total_count = response_data.get('total_count', 0)
                
                if not orders_in_page:
                    logger.info("No more recent orders found in this time range.")
                    break
                    
                total_orders_fetched += len(orders_in_page)
                logger.info(f"Fetched {len(orders_in_page)} recent orders on page {page}. Total fetched: {total_orders_fetched}")
                
                # 4. 转换数据
                for order_raw in orders_in_page:
                    order_transformed = transform_order(order_raw)
                    if order_transformed:
                        all_orders_to_update.append(order_transformed)
                        # 同时转换订单项
                        items_transformed = transform_order_items(order_raw)
                        if items_transformed:
                             all_items_to_update.extend(items_transformed)
                
                # 分页判断
                if len(orders_in_page) < page_size:
                    logger.info("Fetched less orders than page size, assuming last page for status update scan.")
                    break
                
                page += 1
                if page > 500: # Max page limit
                    logger.warning("Reached maximum page limit (500) for status update scan.")
                    break
                time.sleep(0.5) # API rate limit
                
            except (XiaoeAuthError, XiaoeRequestError) as api_error:
                error_message = f"API error during status update fetch page {page}: {api_error}"
                logger.error(error_message, exc_info=True)
                raise
            except Exception as fetch_error:
                error_message = f"Unexpected error during status update fetch page {page}: {fetch_error}"
                logger.error(error_message, exc_info=True)
                raise
                
        # 5. 加载数据到数据库 (UPSERT 会自动更新已有订单/订单项)
        if all_orders_to_update:
            logger.info(f"Upserting {len(all_orders_to_update)} orders for potential status update...")
            upsert_data(db, Order, all_orders_to_update)
        else:
            logger.info("No recent orders found or processed for status update.")

        if all_items_to_update:
            logger.info(f"Upserting {len(all_items_to_update)} order items associated with recent orders...")
            upsert_data(db, OrderItem, all_items_to_update)
        else:
            logger.info("No associated order items found or processed.")

        # 6. 成功处理
        sync_status = "success"
        logger.info(f"{sync_target} completed successfully.")

    except Exception as e:
        sync_status = "failed"
        if not error_message:
            error_message = f"Error during status update processing or upsert: {e}"
        logger.error(f"Xiaoe order status update sync failed: {error_message}", exc_info=True)
    
    finally:
        # 7. 更新同步状态表 (状态更新任务不更新 last_sync_timestamp)
        end_run_time = datetime.now(timezone.utc)
        update_sync_status(db, platform, data_type, mode, 
                           sync_status, error_message, 
                           start_run_time, end_run_time, 
                           None) # 不更新 last_sync_timestamp
        db.close()
        logger.info("Database session closed for status update sync.")

def run_after_sale_sync(full_sync: bool = False):
    """执行小鹅通售后订单的同步（全量或增量）。"""
    logger.info(f"Starting Xiaoe aftersale order sync (Full sync: {full_sync})...")
    start_run_time = datetime.now(timezone.utc)
    platform = "xiaoe"
    data_type = "aftersale"
    # 模式根据 full_sync 标志决定
    mode = "full" if full_sync else "incremental" 
    db = SessionLocal()
    sync_status = "failed" 
    error_message = None
    last_sync_ts = None
    # 对于增量，下次同步的起点；对于全量，此值无意义，但可以记录运行时间
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
            last_sync_ts = get_last_sync_timestamp(db, platform, data_type, mode)
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
            logger.info(f"Fetching page {page} for {data_type} (size={page_size}) from {start_time_str or 'beginning'} to {end_time_str}")
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
        # 更新同步状态表
        end_run_time = datetime.now(timezone.utc)
        update_sync_status(db, platform, data_type, mode, 
                           sync_status, error_message, 
                           start_run_time, end_run_time, 
                           new_last_sync_ts)
        db.close()
        logger.info(f"Database session closed for aftersale sync (mode: {mode}).")

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
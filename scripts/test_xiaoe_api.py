#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地测试小鹅通 API 调用脚本
"""
import sys
import os
import json
from datetime import datetime, timedelta, timezone

# 确保项目根目录在 sys.path 中
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入所需模块 (确保导入路径正确)
try:
    from config.config import settings # 加载配置
    from utils.logger import logger, setup_logging # 使用日志记录器
    from platforms.xiaoe.client import XiaoeClient, XiaoeAuthError, XiaoeRequestError # 导入客户端
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保你在项目根目录下运行此脚本，或者项目结构正确。")
    sys.exit(1)

def run_api_tests():
    """执行 API 调用测试"""
    setup_logging() # 初始化日志

    logger.info("开始本地小鹅通 API 测试...")

    # 检查配置是否加载
    if not all([settings.XIAOE_APP_ID, settings.XIAOE_CLIENT_ID, settings.XIAOE_SECRET_KEY]):
        logger.error("错误：请先在 config/.env 文件中配置完整的小鹅通 API 密钥！")
        return

    client = XiaoeClient()

    try:
        # --- 测试获取订单列表 (get_orders) ---
        logger.info("\n--- 1. 测试获取订单列表 (最近2条) ---")
        orders_data = client.get_orders(page=1, page_size=2) # 获取最近的2条订单试试
        logger.info("获取订单列表 API 返回:")
        # 使用 json.dumps 方便查看复杂结构，ensure_ascii=False 支持中文
        print(json.dumps(orders_data, indent=4, ensure_ascii=False))

        # --- 测试获取售后订单列表 (get_after_sale_orders) ---
        logger.info("\n--- 2. 测试获取售后订单列表 (最近5条，过去15天创建的) ---")
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=15)
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        after_sale_data = client.get_after_sale_orders(
            page=1,
            page_size=5,
            start_time=start_time_str,
            end_time=end_time_str,
            date_type='created_at' # 按创建时间筛选
        )
        logger.info("获取售后订单列表 API 返回:")
        print(json.dumps(after_sale_data, indent=4, ensure_ascii=False))

        # --- 在这里添加其他你想测试的 API 调用 ---
        # 例如:
        # logger.info("\n--- 3. 测试获取单个用户信息 (需要一个有效的 user_id) ---")
        # test_user_id = "用户ID填这里" # 替换成一个你知道的用户ID
        # if test_user_id != "用户ID填这里":
        #     user_info = client.get_user_info(user_id=test_user_id)
        #     logger.info(f"获取用户 {test_user_id} 信息 API 返回:")
        #     print(json.dumps(user_info, indent=4, ensure_ascii=False))
        # else:
        #     logger.warning("请在脚本中提供一个有效的 user_id 来测试 get_user_info")

    except XiaoeAuthError as e:
        logger.error(f"认证或权限错误: {e}")
    except XiaoeRequestError as e:
        logger.error(f"API 请求错误: {e}")
    except Exception as e:
        logger.error(f"发生意外错误: {e}", exc_info=True) # 打印详细的回溯信息

    logger.info("\nAPI 测试结束。")

if __name__ == "__main__":
    run_api_tests()
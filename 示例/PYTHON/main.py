import os
from xiaoe_client import XiaoeClient
import config # 导入配置
import time
from datetime import datetime, timedelta
import json
import csv
import os # 用于检查文件是否存在/大小

# --- 常量定义 ---
CSV_FILENAME = "orders_sync_list_only.csv" # <--- 使用新的 CSV 文件名
TIMESTAMP_STATE_FILE = "last_sync_timestamp_list_only.txt" # <--- 使用新的状态文件名
LIST_API_URL = "https://api.xiaoe-tech.com/xe.order.list.get/1.0.1" # 列表 API
# DETAIL_API_URL = "https://api.xiaoe-tech.com/xe.ecommerce.order.detail/1.0.0" # 详情 API (注释掉)
API_PAGE_SIZE = 50
HISTORY_SYNC_CHUNK_DAYS = 6
# DETAIL_API_DELAY = 0.5 # (注释掉)
INITIAL_HISTORY_START_DATE = "2025-01-01 00:00:00"

# --- 更新：状态/类型码到中文的映射字典 (根据新文档) ---
ORDER_STATE_MAP = {
    0: '未支付',
    1: '支付成功',
    2: '支付失败',
    3: '已退款',
    4: '预付款',
    5: '支付处理中',
    6: '过期自动取消',
    7: '用户手动取消',
    8: '主动全部退款中',
    9: '主动全部退款失败',
    10: '主动全部退款成功',
    11: '发起过部分退款',
}

RESOURCE_TYPE_MAP = { # 使用新文档的值
    0: '无资源(如团购)', 1: '图文', 2: '音频', 3: '视频', 4: '直播',
    5: '会员', 6: '专栏', 7: '圈子', 8: '大专栏', 9: '活动票',
    11: '付费活动票', 16: '付费打卡', 20: '电子书', 21: '实体商品',
    22: '内容市场营销活动', 23: '超级会员', 25: '训练营', 29: '面授课',
    31: '班课', 34: '练习', 35: '班课(重复?)', 41: '有价优惠券',
    42: '课时包', 45: 'AI互动课', 21001: '购物车'
}

SHIP_STATE_MAP = { # 使用新文档的值
    0: '无需发货',
    1: '未发货',
    2: '已发货',
    3: '已收货',
    4: '发起过部分发货',
    # 移除 -1: '无需发货'
}

AFTER_SALES_STATE_MAP = {
    0: '无售后', 1: '处理中', 2: '已处理', 3: '已拒绝',
    4: '已关闭', 5: '待打款', 6: '待买家发货', 7: '待卖家收货',
    8: '退款关闭',
}

# --- 辅助函数：转换金额（分到元）并格式化 ---
def format_currency(amount_in_cents):
    """将分的金额转换为元的字符串，保留两位小数"""
    if isinstance(amount_in_cents, (int, float)):
        return f"{amount_in_cents / 100:.2f}"
    elif isinstance(amount_in_cents, str) and amount_in_cents.isdigit():
         return f"{int(amount_in_cents) / 100:.2f}"
    return amount_in_cents # 如果不是数字或无法转换，返回原始值

def format_yuan_price(price_str):
    """格式化已经是元的金额字符串，确保两位小数"""
    try:
        # 尝试转换为浮点数并格式化
        return f"{float(price_str):.2f}"
    except (ValueError, TypeError):
        # 如果转换失败，返回原始值
        return price_str

# --- 时间戳状态处理函数 ---
def get_last_timestamp(filename=TIMESTAMP_STATE_FILE):
    """从状态文件读取最后处理的 Unix 时间戳"""
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r') as f:
                timestamp_str = f.read().strip()
                print(f"--- 读取到上次状态时间戳: {timestamp_str} ---")
                if timestamp_str.isdigit():
                    return int(timestamp_str)
                else:
                    print(f"--- 状态文件内容非数字: {timestamp_str} ---")
                    return None
        else:
            print("--- 未找到状态文件或为空 ---")
            return None
    except Exception as e:
        print(f"--- 读取状态文件时出错: {e} ---")
        return None

def save_last_timestamp(timestamp, filename=TIMESTAMP_STATE_FILE):
    """将最新的 Unix 时间戳保存到状态文件"""
    try:
        with open(filename, 'w') as f:
            f.write(str(timestamp))
        print(f"--- 已保存最新状态时间戳: {timestamp} ---")
    except Exception as e:
        print(f"--- 保存状态文件时出错: {e} ---")

def datetime_to_timestamp(dt_str):
    """将 'YYYY-MM-DD HH:MM:SS' 格式的字符串转为 Unix 时间戳"""
    if not dt_str or dt_str.startswith('0000'): return 0
    try:
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return int(time.mktime(dt_obj.timetuple()))
    except ValueError:
         print(f"--- 无法解析日期时间字符串: {dt_str} ---")
         return 0

# --- CSV 写入函数 (应用转换和映射 - 更新版) ---
def write_orders_to_csv(orders, filename=CSV_FILENAME):
    """将订单列表追加写入 CSV 文件 (更新中文表头, price按元处理, 其他金额转元, 状态映射)"""
    if not orders: print("--- CSV: 没有新的订单数据需要写入 CSV ---"); return
    print(f"--- CSV: 准备写入 {len(orders)} 条订单到 {filename} ---")

    # 更新 header_map，移除 discount_price，更新中文描述
    header_map = {
        'order_id': '订单ID',
        'created_time': '创建时间',
        'pay_time': '支付时间',
        'order_state': '订单状态',
        'price': '实付金额(元)', # price 单位是元
        'title': '商品标题',
        'user_id': '用户ID',
        'receiver_name': '收货人姓名',
        'receiver_phone': '收货人手机号',
        'receiver_detail': '收货人详细地址',
        'resource_id': '资源ID',
        'resource_type': '资源类型',
        'count': '商品数量',
        'coupon_price': '优惠券抵扣金额(元)', # 假设单位是分，转为元
        # 'discount_price': '折扣金额(元)', # <--- 移除
        'refund_money': '退款金额(元)', # 假设单位是分，转为元
        'refund_time': '退款时间',
        'pay_way': '支付方式码',
        'client_type': '客户端类型码',
        'collection_way': '收款途径码',
        'ship_state': '发货状态',
        'after_sales_state': '售后状态码', # 保留码，不用映射名称
        'out_order_id': '外部订单号',
        'transaction_id': '支付流水号',
        'system_info': '系统信息',
        'team_buy_state': '拼团状态码',
        'sales_state': '分销状态码',
        'settle_time': '结算时间',
    }

    original_fieldnames = list(header_map.keys())
    chinese_fieldnames = list(header_map.values())

    file_exists = os.path.exists(filename)
    is_empty = not file_exists or os.path.getsize(filename) == 0

    try:
        print(f"--- CSV: 打开文件 {filename} (追加模式) ---")
        with open(filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=original_fieldnames, extrasaction='ignore')

            if is_empty:
                header_writer = csv.writer(csvfile)
                header_writer.writerow(chinese_fieldnames)
                print(f"--- CSV: 文件为空，已写入中文表头 ---")

            processed_rows = []
            for order in orders:
                processed_order = {}
                for field in original_fieldnames:
                    raw_value = order.get(field, '')
                    # --- 应用转换和映射 (区分 price) ---
                    if field == 'price':
                        # price 已经是元，直接格式化
                        processed_order[field] = format_yuan_price(raw_value)
                    elif field == 'coupon_price' or field == 'refund_money':
                        # 这些假设是分，需要转换
                        processed_order[field] = format_currency(raw_value)
                    # (移除 discount_price 的处理逻辑)
                    elif field == 'order_state':
                        processed_order[field] = ORDER_STATE_MAP.get(raw_value, raw_value) # 找不到映射则保留原码
                    elif field == 'resource_type':
                        processed_order[field] = RESOURCE_TYPE_MAP.get(raw_value, raw_value)
                    elif field == 'ship_state':
                        processed_order[field] = SHIP_STATE_MAP.get(raw_value, raw_value)
                    elif field == 'after_sales_state':
                        # 保留原始码，不使用映射
                        processed_order[field] = raw_value
                    else:
                        processed_order[field] = raw_value # 其他字段直接使用
                processed_rows.append(processed_order)

            print(f"--- CSV: 准备写入 {len(processed_rows)} 行转换后的数据 ---")
            writer.writerows(processed_rows)
            print(f"--- CSV: 成功将 {len(orders)} 条订单追加写入完毕 ---")
    except Exception as e: print(f"--- CSV: 写入 CSV 文件时出错: {e} ---")

# --- 订单详情获取函数 (注释掉) ---
# def get_order_details(client, order_id):
#     """调用详情 API 获取单个订单的详细信息 (注释掉)"""
#     print(f"--- 正在获取订单详情: {order_id} ---")
#     data = {"order_id": order_id}
#     try:
#         response_text = client.request('post', DETAIL_API_URL, data)
#         if not response_text: print(f"--- 获取订单详情 {order_id} 失败，未收到响应 ---"); return None
#         response_data = json.loads(response_text)
#         if response_data.get("code") == 0:
#             detail_data = response_data.get("data", {}); print(f"--- 成功获取订单详情: {order_id} ---")
#             extracted_details = {}
#             order_info = detail_data.get("order_info", {})
#             ship_info = detail_data.get("delivery_info", {}).get("shipment_list", [{}])[0].get("ship_info",{}) if detail_data.get("delivery_info", {}).get("shipment_list") else {}
#             goods_info_list = detail_data.get("goods_info", {}).get("goods_list", [{}])
#             goods_info = goods_info_list[0] if goods_info_list else {}
#             extracted_details['receiver_name'] = ship_info.get("receiver"); extracted_details['receiver_phone'] = ship_info.get("phone")
#             extracted_details['province'] = ship_info.get("province"); extracted_details['city'] = ship_info.get("city")
#             extracted_details['county'] = ship_info.get("county"); extracted_details['detail_address'] = ship_info.get("detail")
#             extracted_details['spu_id'] = goods_info.get("spu_id"); extracted_details['sku_id'] = goods_info.get("sku_id")
#             extracted_details['goods_name'] = goods_info.get("goods_name")
#             extracted_details['order_state_description'] = order_info.get("order_state_description")
#             extracted_details['payment_type_description'] = order_info.get("payment_type_description")
#             shipment_list = detail_data.get("delivery_info", {}).get("shipment_list", [])
#             extracted_details['ship_state_description'] = shipment_list[0].get("ship_state_description", "") if shipment_list else order_info.get("order_state_description", "")
#             return extracted_details
#         else:
#             print(f"--- 获取订单详情 {order_id} API 错误: code={response_data.get('code')}, msg={response_data.get('msg')} ---"); return None
#     except json.JSONDecodeError: print(f"--- 获取订单详情 {order_id} 响应非 JSON ---"); print(response_text); return None
#     except Exception as e: print(f"--- 获取订单详情 {order_id} 出错: {e} ---"); return None

# --- 主逻辑函数 (改为逐页写入) ---
def fetch_and_process_orders(client, start_ts, end_ts):
    """获取指定时间范围内的所有订单（仅列表 API），逐页写入 CSV
       返回: (bool: 是否成功, int: 最新的订单创建时间戳用于保存状态, 或 start_ts 如果失败)
    """
    # orders_from_list_api = [] # 不再需要累积整个块
    current_page = 1
    total_orders_processed_list = 0
    latest_order_timestamp_in_chunk = start_ts
    success_flag = True
    any_orders_processed_in_chunk = False # 新增：标记本块是否实际处理过订单

    print(f"--- FETCH: 开始处理订单块，时间范围: {start_ts} -> {end_ts} (仅列表, 逐页写入) ---")

    while True: # 列表分页循环
        print(f"--- FETCH: 正在获取列表第 {current_page} 页 ---")
        list_data_payload = {"begin_time": start_ts, "end_time": end_ts, "page_size": API_PAGE_SIZE, "page": current_page}
        print(f"--- FETCH: 列表请求 data={list_data_payload} ---")
        response_text = client.request('post', LIST_API_URL, list_data_payload)
        if not response_text: print("--- FETCH: 列表 API 请求失败，未收到响应 ---"); success_flag = False; break

        try:
            response_data = json.loads(response_text)
            if response_data.get("code") == 0:
                print("--- FETCH: 列表 API 请求成功 (code=0) ---")
                api_data = response_data.get("data", {}); orders_list = api_data.get("list", []); total_count = api_data.get("total", 0)
                if not orders_list: print(f"--- FETCH: 第 {current_page} 页列表未获取到订单数据 ---"); break
                print(f"--- FETCH: 第 {current_page} 页列表获取到 {len(orders_list)} 条订单摘要，总数 {total_count} ---")
                print(f"--- FETCH: 本页订单 IDs (部分): {[o.get('order_id') for o in orders_list[:3]]} ... ---")

                # --- 逐页写入 CSV --- START
                print(f"--- FETCH: 准备写入第 {current_page} 页的 {len(orders_list)} 条数据到 CSV --- ")
                write_orders_to_csv(orders_list, CSV_FILENAME)
                any_orders_processed_in_chunk = True # 标记有数据被处理
                # --- 逐页写入 CSV --- END

                # 更新时间戳 (仍然基于本页数据)
                for order_summary in orders_list:
                    created_ts = datetime_to_timestamp(order_summary.get('created_time', ''))
                    if created_ts > 0 and created_ts > latest_order_timestamp_in_chunk: latest_order_timestamp_in_chunk = created_ts

                total_orders_processed_list += len(orders_list)
                if len(orders_list) < API_PAGE_SIZE: print("--- FETCH: 列表 API 当前页返回订单数小于页面大小，假定已是最后一页 ---"); break
                elif total_count > 0 and total_orders_processed_list >= total_count: print(f"--- FETCH: 已获取列表订单数 ({total_orders_processed_list}) >= 总数 ({total_count}) --"); break
                current_page += 1
            else:
                print(f"--- FETCH: 列表 API 返回错误: code={response_data.get('code')}, msg={response_data.get('msg')} ---"); success_flag = False; break
        except json.JSONDecodeError: print("--- FETCH: 列表 API 响应内容不是 JSON ---"); print(response_text); success_flag = False; break
        except Exception as e: print(f"--- FETCH: 处理列表 API 响应时出错: {e} ---"); success_flag = False; break

    # 列表分页处理完毕
    print(f"--- FETCH: 时间块分页处理完成 --- ")
    if success_flag:
        # print("--- FETCH: 准备调用 CSV 写入函数 (仅列表数据) --- ") # 调用已移入循环内
        # write_orders_to_csv(orders_from_list_api, CSV_FILENAME) # 不再需要最后写入
        if any_orders_processed_in_chunk: # 如果这个块处理过订单
            print(f"--- FETCH: 返回成功，本块最新时间戳 {latest_order_timestamp_in_chunk} ---")
            return True, latest_order_timestamp_in_chunk
        else: # 成功但本块无订单
            print(f"--- FETCH: 返回成功，本块无新订单，下次从块结束时间 {end_ts} 开始 ---")
            return True, end_ts
    else:
        print(f"--- FETCH: 处理失败，返回失败状态，下次从块开始时间 {start_ts} 重试 ---")
        return False, start_ts

# --- 主循环 (处理历史分块 - 保持不变) ---
if __name__ == "__main__":
    print("--- 初始化 XiaoeClient ---")
    client = XiaoeClient()
    print("--- XiaoeClient 初始化完成 ---")

    # 确定历史同步的起始和结束时间
    initial_start_dt = datetime.strptime(INITIAL_HISTORY_START_DATE, '%Y-%m-%d %H:%M:%S')
    initial_start_ts = int(time.mktime(initial_start_dt.timetuple()))
    final_end_ts = int(time.mktime(datetime.now().timetuple()))
    print(f"--- 目标历史同步范围: {initial_start_dt.strftime('%Y-%m-%d %H:%M:%S')} ({initial_start_ts}) -> 现在 ({final_end_ts}) ---")

    # 尝试从状态文件恢复上次进度
    current_sync_start_ts = get_last_timestamp(TIMESTAMP_STATE_FILE) # 使用新的状态文件名
    if current_sync_start_ts is None or current_sync_start_ts < initial_start_ts:
        print(f"--- 从初始日期 {INITIAL_HISTORY_START_DATE} 开始同步 --- ")
        current_sync_start_ts = initial_start_ts
    else:
        current_sync_start_ts += 1
        print(f"--- 从上次保存的时间点 {current_sync_start_ts} 继续同步 ---")

    # 按 HESTORY_SYNC_CHUNK_DAYS 天分块处理历史数据
    while current_sync_start_ts < final_end_ts:
        try:
            chunk_end_ts = current_sync_start_ts + (HISTORY_SYNC_CHUNK_DAYS * 24 * 60 * 60) - 1
            chunk_end_ts = min(chunk_end_ts, final_end_ts)
            print(f"\n--- === 处理时间块: {datetime.fromtimestamp(current_sync_start_ts)} -> {datetime.fromtimestamp(chunk_end_ts)} (仅列表) === ---")

            success, last_processed_ts_in_chunk = fetch_and_process_orders(client, current_sync_start_ts, chunk_end_ts)

            if success:
                save_last_timestamp(last_processed_ts_in_chunk, TIMESTAMP_STATE_FILE) # 使用新的状态文件名
                current_sync_start_ts = chunk_end_ts + 1
            else:
                print("--- 处理时间块失败，中断历史同步 --- ")
                break

        except KeyboardInterrupt:
            print("\n--- 检测到手动中断，退出历史同步 --- ")
            break
        except Exception as e:
            print(f"\n--- 历史同步主循环遇到未处理的异常: {e} ---")
            print("--- 中断历史同步，请检查错误 --- ")
            break

    print("--- === 历史订单同步完成或中断 (仅列表数据) === ---")

    # 可以在这里添加持续运行的逻辑（如果需要的话），
    # 例如，使用之前的 LOOP_DELAY_SECONDS 和增量更新逻辑。
    # 但当前版本设计为完成历史同步后即退出。
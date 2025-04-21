"""
小鹅通 API 数据转换工具 (适配新架构)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from utils.logger import logger

PLATFORM_NAME = "xiaoe"

def _parse_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """尝试将多种格式的日期时间字符串解析为带时区的 datetime 对象 (UTC)。"""
    if not datetime_str or datetime_str == "0000-00-00 00:00:00": # 处理空或无效时间
        return None
    # 常见的格式列表
    formats = [
        "%Y-%m-%d %H:%M:%S", # e.g., 2023-10-27 15:30:00
        "%Y-%m-%dT%H:%M:%S%z", # ISO 8601 with timezone, e.g., 2023-10-27T15:30:00+0800
        "%Y-%m-%dT%H:%M:%S.%f%z", # ISO 8601 with microsecond and timezone
        "%Y/%m/%d %H:%M:%S", # e.g., 2023/10/27 15:30:00
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            continue
    logger.warning(f"Could not parse datetime string: {datetime_str} with known formats.")
    return None

def _safe_float_convert(value: Any, default: float = 0.0) -> float:
    """安全地将值转换为 float，处理 None 或转换失败的情况。"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to float: {value}. Using default {default}.")
        return default

def _safe_int_convert(value: Any, default: int = 0) -> int:
    """安全地将值转换为 int，处理 None 或转换失败的情况。"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to int: {value}. Using default {default}.")
        return default

def transform_order(order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换订单数据格式 (适配 xe.ecommerce.order.list/1.0.0 返回结构).
    """
    order_info = order_data.get('order_info')
    price_info = order_data.get('price_info')

    if not order_info or not price_info or not order_info.get('order_id') or not order_info.get('user_id'):
        logger.warning(f"Skipping order transformation due to missing key fields in order_info or price_info: {order_data}")
        return None

    # 小鹅通价格单位是分，需要转为元
    price = _safe_float_convert(price_info.get('actual_price'), 0) / 100 # 实付金额
    coupon_price = _safe_float_convert(order_info.get('discount_amount'), 0) / 100 # 优惠金额
    refund_money = _safe_float_convert(order_info.get('refund_fee'), 0) / 100 # 退款金额

    transformed = {
        'platform': PLATFORM_NAME,
        'order_id': order_info.get('order_id'),
        'user_id': order_info.get('user_id'),
        'price': price,
        'coupon_price': coupon_price,
        'refund_money': refund_money,
        'order_state': _safe_int_convert(order_info.get('order_state'), 0),
        # 尝试获取 order_state_text，如果API不直接提供，可能需要映射
        # 'order_state_text': order_info.get('order_state_text'),
        # resource_type 不在 order_info 中，可能在 good_list 里，或者需要忽略
        # 'resource_type': _safe_int_convert(order_info.get('resource_type'), 0),
        # 'resource_type_text': order_info.get('resource_type_text'),

        # 转换日期时间
        'pay_time': _parse_datetime(order_info.get('pay_state_time')), # 使用支付状态时间作为支付时间
        'created_at': _parse_datetime(order_info.get('created_time')), # 使用订单创建时间
    }

    if transformed['created_at'] is None:
         logger.error(f"Order {transformed['order_id']} skipped: missing or invalid created_time (created_at) field.")
         return None

    return transformed

def transform_order_items(order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从订单数据中提取并转换订单商品数据 (适配 xe.ecommerce.order.list/1.0.0 结构).
    """
    order_info = order_data.get('order_info')
    if not order_info or not order_info.get('order_id'):
        logger.warning("Cannot transform order items without order_id in order_info.")
        return []

    order_id = order_info['order_id']
    good_list = order_data.get('good_list', []) # 商品信息在 good_list 中
    if not isinstance(good_list, list):
        logger.warning(f"good_list is not a list for order {order_id}. Skipping items.")
        return []

    items = []
    for resource in good_list:
        # 商品 ID 可能在 resource_id 或 spu_id
        product_id = resource.get('resource_id') or resource.get('spu_id')
        if not isinstance(resource, dict) or not product_id:
            logger.warning(f"Skipping invalid resource item in order {order_id}: {resource}")
            continue

        item = {
            'platform': PLATFORM_NAME,
            'order_id': order_id,
            'product_id': product_id,
            'product_name': resource.get('goods_name'),
            'quantity': _safe_int_convert(resource.get('buy_num'), 1), # 数量是 buy_num
            'price': _safe_float_convert(resource.get('unit_price'), 0) / 100 # 单价是 unit_price (分转元)
        }
        items.append(item)

    return items

def transform_user(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换用户数据格式，匹配 User 模型。

    Args:
        user_data: 小鹅通 API 返回的原始用户数据字典。

    Returns:
        标准化后的用户数据字典，如果关键字段缺失则返回 None。
    """
    if not user_data or not user_data.get('user_id'):
        logger.warning(f"Skipping user transformation due to missing user_id: {user_data}")
        return None

    transformed = {
        'platform': PLATFORM_NAME,
        'user_id': user_data.get('user_id'),
        'nickname': user_data.get('nickname'),
        'avatar': user_data.get('avatar'),
        'mobile': user_data.get('mobile'), # 脱敏应在存储或展示层处理
        # 'email': user_data.get('email'),
        # 'gender': _safe_int_convert(user_data.get('gender')),
        # 'birthday': _parse_datetime(user_data.get('birthday')), # API返回的是日期还是时间戳?
        # 'province': user_data.get('province'),
        # 'city': user_data.get('city'),
        'register_time': _parse_datetime(user_data.get('register_time'))
        # updated_at 由数据库自动处理
    }
    return transformed

def transform_product(product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换商品数据格式，匹配 Product 模型。

    Args:
        product_data: 小鹅通 API 返回的原始商品数据字典。

    Returns:
        标准化后的商品数据字典，如果关键字段缺失则返回 None。
    """
    # 商品接口返回的 ID 字段是 goods_id，模型中是 product_id
    product_id = product_data.get('goods_id') 
    if not product_data or not product_id:
        logger.warning(f"Skipping product transformation due to missing goods_id: {product_data}")
        return None

    transformed = {
        'platform': PLATFORM_NAME,
        'product_id': product_id,
        'title': product_data.get('title'),
        # 'sub_title': product_data.get('sub_title'), # 模型中没有此字段
        'price': _safe_float_convert(product_data.get('price'), 0) / 100, # 分转元
        # 'original_price': _safe_float_convert(product_data.get('original_price'), 0) / 100, # 模型中没有此字段
        'type': _safe_int_convert(product_data.get('type'), 0), # 对应模型中的 `type` 列
        'cover_img': product_data.get('cover_img'),
        'status': _safe_int_convert(product_data.get('status'), 0),
        'created_at': _parse_datetime(product_data.get('created_at'))
        # updated_at 由数据库自动处理
    }
    return transformed 
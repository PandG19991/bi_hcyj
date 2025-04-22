"""
小鹅通 API 数据转换工具 (适配新架构)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import re
import json # 导入 json 用于处理 JSON 字段
from decimal import Decimal, InvalidOperation # 导入 Decimal

from utils.logger import logger

PLATFORM_NAME = "xiaoe"

# 定义映射关系
ORDER_STATE_MAP = {
    0: '待付款',
    1: '待成交',  # 注意：文档中是"待成交"，通常理解为"已付款待处理"或类似状态
    2: '待发货',
    3: '已发货',
    4: '已完成',
    5: '已关闭'
}

RESOURCE_TYPE_MAP = {
    0: '知识商品',
    1: '实物商品',
    2: '服务类商品',
    3: '打赏',
    4: '红包'
}

# 新增售后订单状态映射 (根据文档和通用理解)
AFTER_SALE_STATE_TO_ORDER_STATE_MAP = {
    2: (5, "已关闭(售后)"),  # 售后成功 -> 订单已关闭
    # 1: 待商家处理 - 不改变主订单状态
    # 3: 已撤销 - 不改变主订单状态
    # 6: 售后中 - 不改变主订单状态
    # 可以根据需要扩展其他状态映射
}

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
            # 假设API返回的时间是本地时间（如北京时间），需要转换为UTC存储
            # 如果API返回的是UTC时间，则不需要 astimezone(timezone.utc)
            # 这里假设输入是本地时间，如果需要按原样存储或已知是UTC，则调整逻辑
            if dt.tzinfo is None:
                # 如果没有时区信息，根据实际情况决定是视为UTC还是本地时间
                # 假设视为本地时间，需要有方法获取本地时区，或者配置时区
                # 简化处理：暂且视为 UTC，如果需要本地转UTC，需要引入时区库（如pytz, zoneinfo）
                 dt = dt.replace(tzinfo=timezone.utc) # 简单处理为 UTC
            else:
                dt = dt.astimezone(timezone.utc) # 转换到 UTC
            return dt
        except ValueError:
            continue
    logger.warning(f"Could not parse datetime string: {datetime_str} with known formats.")
    return None

def _safe_decimal_convert(value: Any, default_str: str = '0.00', scale: int = 100) -> Decimal:
    """安全地将值转换为 Decimal，处理 None、空字符串或转换失败的情况，并处理分到元的转换。"""
    if value is None or value == '':
        return Decimal(default_str)
    try:
        # 先尝试直接转 Decimal (如果已经是元)
        # 如果失败，再尝试转 float 再除以 scale (处理分)
        try:
            # 处理字符串形式的 Decimal
            return Decimal(value).quantize(Decimal('0.01')) # 确保两位小数
        except InvalidOperation:
            # 处理数字或数字字符串形式的分
            num_value = float(value)
            # 使用字符串避免浮点数精度问题
            return (Decimal(str(num_value)) / Decimal(str(scale))).quantize(Decimal('0.01'))
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.warning(f"Could not convert value {repr(value)} to Decimal. Error: {e}. Using default {default_str}.")
        return Decimal(default_str)

def _safe_int_convert(value: Any, default: Optional[int] = None) -> Optional[int]: # 默认返回 None
    """安全地将值转换为 int，处理 None 或转换失败的情况。失败时返回 None。"""
    if value is None or value == '':
        return default
    try:
        # 先尝试转 float 再转 int，兼容 '1.0' 这种情况
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value {repr(value)} to int. Returning default {default}.")
        return default

def _safe_string(value: Any) -> Optional[str]:
    """确保值是字符串，如果是 None 则返回 None。"""
    if value is None:
        return None
    return str(value)

def _safe_json_parse(value: Any) -> Optional[Any]:
    """尝试解析 JSON 字符串，失败则返回原始值或 None。"""
    if isinstance(value, (dict, list)): # 如果已经是 dict 或 list，直接返回
        return value
    if isinstance(value, str):
        try:
            # 处理可能的空字符串或 "null"
            if not value or value.lower() == 'null':
                return None
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON string: {value[:100]}...")
            return None # 解析失败返回 None
    return value # 其他类型直接返回

def transform_order(order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换订单数据格式 (适配 xe.ecommerce.order.list/1.0.0 返回结构)
    使其字段和类型匹配 core/models.py 中的 Order 模型。
    """
    # 根据文档结构获取子对象，使用 .get 提供默认空字典
    order_info = order_data.get('order_info', {})
    price_info = order_data.get('price_info', {})
    payment_info = order_data.get('payment_info', {})
    ship_info_api = order_data.get('ship_info', {}) # 重命名避免与模型字段冲突
    buyer_info = order_data.get('buyer_info', {})
    goods_info = order_data.get('goods_info', {})
    good_list = goods_info.get('goods_list', [])

    # 核心 ID 检查
    order_id = order_info.get('order_id')
    user_id = buyer_info.get('user_id') # 用户ID在 buyer_info 中

    if not order_id or not user_id:
        logger.warning(f"Skipping order transformation due to missing order_id or user_id: order_info={order_info}, buyer_info={buyer_info}")
        return None

    # --- 提取和转换字段 (根据文档调整路径和字段名) --- 
    transformed = {
        'platform': PLATFORM_NAME,
        'order_id': order_id,
        'user_id': user_id,
        'app_id': _safe_string(order_info.get('app_id')),

        # 状态码
        'order_state': _safe_int_convert(order_info.get('order_state')),
        'pay_state': _safe_int_convert(order_info.get('pay_state')),
        'order_type': _safe_int_convert(order_info.get('order_type')),
        'sub_order_type': _safe_int_convert(order_info.get('sub_order_type')),
        'aftersale_show_state': _safe_int_convert(order_info.get('aftersale_show_state')),
        'settle_state': _safe_int_convert(order_info.get('settle_state')),
        'check_state': _safe_int_convert(order_info.get('check_state')),
        'order_close_type': _safe_int_convert(order_info.get('order_close_type')),
        'is_deleted': bool(_safe_int_convert(order_info.get('is_deleted'), default=0)), # 文档说是 boolean? 确认实际类型

        # 价格 (来自 order_info, 单位：分)
        'actual_fee': _safe_decimal_convert(order_info.get('actual_fee')),
        'goods_original_total_price': _safe_decimal_convert(order_info.get('goods_original_total_price')),
        'discount_amount': _safe_decimal_convert(order_info.get('discount_amount')),
        'freight_actual_price': _safe_decimal_convert(order_info.get('freight_actual_price')),
        'freight_original_price': _safe_decimal_convert(order_info.get('freight_original_price')),
        'modified_amount': _safe_decimal_convert(order_info.get('modified_amount')),
        'deduct_amount': _safe_decimal_convert(order_info.get('deduct_amount')),
        'refund_fee': _safe_decimal_convert(order_info.get('refund_fee')),

        # 时间 (来自 order_info)
        'created_at_platform': _parse_datetime(order_info.get('created_at') or order_info.get('create_time')), # 文档没有 created_time，确认实际字段
        'pay_state_time': _parse_datetime(order_info.get('pay_state_time')),
        'order_state_time': _parse_datetime(order_info.get('order_state_time')),
        'aftersale_show_state_time': _parse_datetime(order_info.get('aftersale_show_state_time')),
        'settle_state_time': _parse_datetime(order_info.get('settle_state_time')),
        'refund_time': _parse_datetime(order_info.get('refund_time')),
        'update_time_platform': _parse_datetime(order_info.get('update_time')),

        # 商品概览 (来自 order_info)
        'goods_buy_num': _safe_int_convert(order_info.get('goods_buy_num'), default=0),
        'goods_name_overview': _safe_string(order_info.get('goods_name'))[:1000], # 使用 order_info.goods_name
        'goods_spu_type': _safe_int_convert(order_info.get('goods_spu_type')),
        'goods_spu_sub_type': _safe_string(order_info.get('goods_spu_sub_type')),

        # 渠道与来源 (来自 order_info)
        'channel_type': _safe_int_convert(order_info.get('channel_type')),
        'channel_bus_id': _safe_string(order_info.get('channel_bus_id')),
        'source': _safe_int_convert(order_info.get('source')),
        'wx_app_type': _safe_int_convert(order_info.get('wx_app_type')),

        # 关联信息 (来自 order_info)
        'relation_order_type': _safe_int_convert(order_info.get('relation_order_type')),
        'relation_order_id': _safe_string(order_info.get('relation_order_id')),
        'relation_order_appid': _safe_string(order_info.get('relation_order_appid')),

        # 支付信息 (来自 payment_info 和 order_info)
        'pay_type': _safe_int_convert(order_info.get('pay_type')),
        'out_order_id_payment': _safe_string(payment_info.get('out_order_id')),
        'third_order_id': _safe_string(payment_info.get('third_order_id')),
        'trade_id': _safe_string(order_info.get('trade_id')),

        # 分销/活动信息 (来自 order_info)
        'share_type': _safe_int_convert(order_info.get('share_type')),
        'share_user_id': _safe_string(order_info.get('share_user_id')),
        # 直接存储数组，因为模型字段是 JSON
        'distribute_type_bitmap': order_info.get('distribute_type_bitmap'),
        'activity_type_bitmap': order_info.get('activity_type_bitmap'),

        # 物流相关 (来自 order_info 和 ship_info_api)
        'ship_way_choose_type': _safe_int_convert(order_info.get('ship_way_choose_type')),
        'ship_info': ship_info_api, # 存储整个 ship_info 对象

        # 备注信息 (来自 buyer_info)
        'user_comment': _safe_string(buyer_info.get('user_comment')),
        'merchant_remark': None, # 文档中未找到商家备注字段

        # 其他 (来自 order_info)
        'use_collection': _safe_int_convert(order_info.get('use_collection')),
    }

    # 关键时间戳检查 (使用 created_at_platform)
    if transformed['created_at_platform'] is None:
         logger.error(f"Order {transformed['order_id']} skipped: missing or invalid create_time/created_at_platform field.")
         return None

    return transformed

def transform_order_items(order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从订单数据中提取并转换订单商品数据 (适配 xe.ecommerce.order.list/1.0.0 结构)
    使其字段和类型匹配 core/models.py 中的 OrderItem 模型。
    """
    order_info = order_data.get('order_info', {})
    goods_info = order_data.get('goods_info', {})
    order_id = order_info.get('order_id')

    if not order_id:
        logger.warning("Cannot transform order items without order_id in order_info.")
        return []

    good_list = goods_info.get('goods_list', [])
    if not isinstance(good_list, list):
        logger.warning(f"goods_list is not a list for order {order_id}. Skipping items.")
        return []

    items = []
    for resource in good_list:
        # 商品 ID 使用 spu_id 或 resource_id
        product_id = resource.get('spu_id') or resource.get('resource_id')
        if not isinstance(resource, dict) or not product_id:
            logger.warning(f"Skipping invalid resource item in order {order_id}: {resource}")
            continue

        item = {
            'platform': PLATFORM_NAME,
            'order_id': order_id,
            'product_id': _safe_string(product_id),
            # OrderItem 模型字段映射 (根据 get_order_list.md goods_list)
            # 'item_id': _safe_string(resource.get('item_id')), # 文档无此字段
            'resource_id': _safe_string(resource.get('resource_id')),
            'resource_type': _safe_int_convert(resource.get('resource_type')),
            'goods_name': _safe_string(resource.get('goods_name')),
            'goods_image': _safe_string(resource.get('goods_image')),
            'goods_desc': _safe_string(resource.get('goods_desc')),
            'goods_sn': _safe_string(resource.get('goods_sn')),
            'spu_type': _safe_string(resource.get('spu_type')),

            # SKU 信息
            'sku_id': _safe_string(resource.get('sku_id')),
            'sku_spec_code': _safe_string(resource.get('sku_spec_code')),
            'goods_spec_desc': _safe_string(resource.get('goods_spec_desc')),

            # 数量与价格 (分转元, 使用 Decimal)
            # !! 文档中 goods_list 没有明确的购买数量字段 (如 buy_num) !!
            # !! 需要确认此字段来源，否则 quantity 无法正确设置 !!
            # !! 暂时假设存在 buy_num 字段
            'quantity': _safe_int_convert(resource.get('buy_num'), default=1), # 假设存在 buy_num
            'unit_price': _safe_decimal_convert(resource.get('unit_price')),
            'total_price': _safe_decimal_convert(resource.get('total_price')),
            'discount_amount': _safe_decimal_convert(resource.get('discount_amount')),
            'actual_fee': _safe_decimal_convert(resource.get('actual_fee')),
            'discount_detail': _safe_json_parse(resource.get('discount_detail')), # 文档是 array

            # 有效期
            'period_type': _safe_int_convert(resource.get('period_type')),
            'expire_desc': _safe_string(resource.get('expire_desc')),
            'expire_start': _parse_datetime(resource.get('expire_start')),
            'expire_end': _parse_datetime(resource.get('expire_end')),

            # 状态
            'check_state': _safe_int_convert(resource.get('check_state')),
            'check_state_desc': _safe_string(resource.get('check_state_desc')),
            'refund_state': _safe_int_convert(resource.get('refund_state')),
            'refund_state_desc': _safe_string(resource.get('refund_state_desc')),
            'ship_state': _safe_int_convert(resource.get('ship_state')),
            'ship_state_desc': _safe_string(resource.get('ship_state_desc')),

            # 关联信息
            'relation_goods_id': _safe_string(resource.get('relation_goods_id')),
            'relation_goods_type': _safe_int_convert(resource.get('relation_goods_type')),
            'relation_goods_type_desc': _safe_string(resource.get('relation_goods_type_desc')),
        }
        items.append(item)

    return items

def transform_user(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换用户数据格式，匹配 User 模型。
    基于 /xe.user.info.batch.get/1.0.0 或 /xe.user.info.get/1.0.0 返回结构。

    Args:
        user_data: 小鹅通 API 返回的原始用户数据字典。

    Returns:
        标准化后的用户数据字典，如果关键字段缺失则返回 None。
    """
    user_id = user_data.get('user_id')
    if not user_data or not user_id:
        logger.warning(f"Skipping user transformation due to missing user_id: {user_data}")
        return None

    transformed = {
        'platform': PLATFORM_NAME,
        'user_id': user_id,
        'nickname': _safe_string(user_data.get('nickname')),
        'avatar': _safe_string(user_data.get('avatar')),
        'phone': _safe_string(user_data.get('phone')), # 批量接口直接是 phone
        'register_time': _parse_datetime(user_data.get('register_time')) # 批量接口是 register_time
        # first_seen_at 和 last_updated_at 由数据库自动处理
    }
    return transformed

def transform_product(product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换商品数据格式，匹配 Product 模型。
    基于 /xe.goods.relations.get/2.0.0 返回结构。

    Args:
        product_data: 小鹅通 API 返回的原始商品数据字典。

    Returns:
        标准化后的商品数据字典，如果关键字段缺失则返回 None。
    """
    # 商品 ID 使用 id, resource_id 或 spu_id
    product_id = product_data.get('id') or product_data.get('resource_id') or product_data.get('spu_id')
    if not product_data or not product_id:
        logger.warning(f"Skipping product transformation due to missing id/resource_id/spu_id: {product_data}")
        return None

    # 从 goods_img 数组获取图片 URL
    goods_imgs = product_data.get('goods_img', [])
    img_url = goods_imgs[0] if isinstance(goods_imgs, list) and goods_imgs else None

    transformed = {
        'platform': PLATFORM_NAME,
        'product_id': _safe_string(product_id),
        'name': _safe_string(product_data.get('goods_name')), # API 字段是 goods_name
        'type': _safe_int_convert(product_data.get('resource_type')), # API 字段是 resource_type
        'type_desc': _safe_string(product_data.get('spu_type')), # 存储 spu_type 字符串
        'img_url': _safe_string(img_url), # 从 goods_img[0] 获取

        # 新增字段转换
        'price_low': _safe_decimal_convert(product_data.get('price_low')),
        'price_high': _safe_decimal_convert(product_data.get('price_high')),
        'status': _safe_int_convert(product_data.get('sale_status')),
        'created_at_platform': _parse_datetime(product_data.get('created_at')),
        'updated_at_platform': _parse_datetime(product_data.get('updated_at')),

        # first_seen_at 和 last_updated_at 由数据库自动处理
    }
    return transformed

def transform_after_sale_order(after_sale_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换售后订单数据，匹配 AftersaleOrder 模型。
    基于 /xe.aftersale.list/1.0.0 返回结构。
    """
    aftersale_id = after_sale_data.get('aftersale_id')
    order_id = after_sale_data.get('order_id')
    if not after_sale_data or not order_id or not aftersale_id:
        logger.warning(f"Skipping after-sale transformation due to missing order_id or aftersale_id: {after_sale_data}")
        return None

    # --- 提取和转换字段 --- 
    transformed = {
        'platform': PLATFORM_NAME,
        'aftersale_id': aftersale_id,
        'order_id': order_id,
        # 'user_id': ..., # user_id 需要从关联的 Order 表获取，这里不直接提取

        # 状态与类型
        'state': _safe_int_convert(after_sale_data.get('state')),
        'state_str': _safe_string(after_sale_data.get('state_str')),
        # 'sale_type': ..., # 需要根据 sale_type_name 推断或查找映射关系
        'sale_type_name': _safe_string(after_sale_data.get('sale_type_name')),
        # 'ship_state': ..., # 需要根据 ship_state_str 推断或查找映射关系
        'ship_state_str': _safe_string(after_sale_data.get('ship_state_str')),

        # 金额 (分转元)
        'apply_refund_money': _safe_decimal_convert(after_sale_data.get('apply_refund_money')),
        'refund_money': _safe_decimal_convert(after_sale_data.get('refund_money')),

        # 时间
        'created_at_platform': _parse_datetime(after_sale_data.get('created_at')),
        'updated_at_platform': _parse_datetime(after_sale_data.get('updated_at')),
        'invalid_time': _parse_datetime(after_sale_data.get('invalid_time')),
        'state_invalid_time': _parse_datetime(after_sale_data.get('state_invalid_time')),

        # 原因与备注
        'reason': _safe_string(after_sale_data.get('reason')),
        'state_reason': _safe_string(after_sale_data.get('state_reason')),
        'remark': _safe_string(after_sale_data.get('remark')), # 买家备注
        'merchant_remark': _safe_string(after_sale_data.get('merchant_remark')), # 商家备注

        # 商品概览 (使用 API 直接提供的顶层字段)
        'goods_name_overview': _safe_string(after_sale_data.get('goods_name')),
        'img_url_overview': _safe_string(after_sale_data.get('img_url')),
        'sku_info_overview': _safe_string(after_sale_data.get('sku_info')),
        'resource_type_str': _safe_string(after_sale_data.get('resource_type_str')),

        # 其他
        'use_collection': _safe_int_convert(after_sale_data.get('use_collection')),

        # first_seen_at 和 last_updated_at 由数据库自动处理
    }

    # 补充推断 sale_type 和 ship_state (示例)
    sale_type_name = transformed.get('sale_type_name')
    if sale_type_name == '仅退款':
        transformed['sale_type'] = 1
    elif sale_type_name == '退款退货':
        transformed['sale_type'] = 2
    elif sale_type_name:
        logger.warning(f"Unknown sale_type_name '{sale_type_name}' for aftersale {aftersale_id}. Cannot infer sale_type.")
        transformed['sale_type'] = None # 或者设置一个默认未知值
    else:
        transformed['sale_type'] = None

    # 完善 ship_state 的推断逻辑
    ship_state_str = transformed.get('ship_state_str')
    ship_state_map = {
        "待买家发货": 1,
        "买家已发货": 2,
        "商家已收货": 3,
        "商家未收货": 4,
        "退货入库中": 5, # 假设的，需要确认实际文本
        "已入库": 6,     # 假设的，需要确认实际文本
        # ... 其他状态映射 ...
    }
    if ship_state_str in ship_state_map:
        transformed['ship_state'] = ship_state_map[ship_state_str]
    elif ship_state_str:
        logger.warning(f"Unknown ship_state_str '{ship_state_str}' for aftersale {aftersale_id}. Cannot infer ship_state.")
        transformed['ship_state'] = None # 或者设置一个默认未知值
    else:
        transformed['ship_state'] = None

    return transformed

def transform_aftersale_items(after_sale_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从售后订单数据中提取并转换售后商品数据，匹配 AftersaleItem 模型。
    """
    aftersale_id = after_sale_data.get('aftersale_id')
    if not aftersale_id:
        logger.warning("Cannot transform aftersale items without aftersale_id.")
        return []

    goods_list = after_sale_data.get('goods_list', [])
    if not isinstance(goods_list, list):
        logger.warning(f"goods_list is not a list for aftersale order {aftersale_id}. Skipping items.")
        return []

    items = []
    for good in goods_list:
        if not isinstance(good, dict):
            logger.warning(f"Skipping invalid good item in aftersale order {aftersale_id}: {good}")
            continue

        item = {
            'platform': PLATFORM_NAME,
            'aftersale_id': aftersale_id,
            # AftersaleItem 模型字段映射
            'goods_name': _safe_string(good.get('goods_name')),
            'goods_tag': _safe_string(good.get('goods_tag')),
            'img_url': _safe_string(good.get('img_url')),
            'sku_info': _safe_string(good.get('sku_info')),
            'buy_num': _safe_int_convert(good.get('buy_num')), # 如果 API 未提供，则为 None
            'goods_price': _safe_decimal_convert(good.get('goods_price'), default_str=None), # 如果 API 未提供，则为 None
            # 'order_item_id': ..., # 关联原始订单项需要额外逻辑或 API 支持

            # first_seen_at 和 last_updated_at 由数据库自动处理
        }
        items.append(item)

    return items 
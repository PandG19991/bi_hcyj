import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .logger import logger

# --- Helper Functions ---

def _safe_to_datetime(date_str: Optional[str], format: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime.datetime]:
    """Safely convert a string to a datetime object, handling None and invalid formats."""
    if not date_str or date_str == '0000-00-00 00:00:00' or date_str == '-0001-11-30 00:00:00':
        return None
    try:
        return datetime.datetime.strptime(date_str, format)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date string: {date_str} with format {format}")
        return None

def _safe_to_int(value: Any) -> Optional[int]:
    """Safely convert a value to an integer, handling None and non-integer values."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to int: {value}")
        return None

def _safe_to_float(value: Any) -> Optional[float]:
    """Safely convert a value to a float, handling None and non-numeric values."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to float: {value}")
        return None

def _cents_to_float(cents: Any) -> Optional[float]:
    """Safely convert an integer amount in cents to a float amount in base units."""
    int_cents = _safe_to_int(cents)
    if int_cents is None:
        return None
    return round(int_cents / 100.0, 2)

# --- Main Transformation Functions ---

def transform_user(raw_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transforms raw user data from Xiaoe API into a structured dictionary."""
    if not raw_user or not raw_user.get('user_id'):
        logger.warning("Skipping user transformation due to missing data or user_id.")
        return None
        
    return {
        'user_id': raw_user.get('user_id'), # PK
        'user_nickname': raw_user.get('user_nickname'),
        'bind_phone': raw_user.get('bind_phone'),
        'avatar_url': raw_user.get('avatar'),
        'source': raw_user.get('from'), # API returns description string
        'total_paid_amount': _cents_to_float(raw_user.get('pay_sum')),
        'purchase_count': _safe_to_int(raw_user.get('punch_count')),
        'wx_union_id': raw_user.get('wx_union_id'),
        'wx_open_id': raw_user.get('wx_open_id'),
        'wx_app_open_id': raw_user.get('wx_app_open_id'),
        'created_at': _safe_to_datetime(raw_user.get('user_created_at')),
        # 'last_visited_at': _safe_to_datetime(raw_user.get('latest_visited_at'), '%Y-%m-%d %H:%M:%S.%f') # If requested
    }

def transform_order(raw_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transforms raw order data (from list API) into a structured dictionary."""
    order_info = raw_order.get('order_info', {})
    price_info = raw_order.get('price_info', {})
    ship_info = raw_order.get('ship_info', {})
    promoter_info = raw_order.get('promoter_info', {})
    buyer_info = raw_order.get('buyer_info', {}) # Though user_id is primary link
    
    order_id = order_info.get('order_id')
    if not raw_order or not order_id:
        logger.warning("Skipping order transformation due to missing data or order_id.")
        return None

    # Transform goods list within the order
    transformed_goods_list = []
    raw_goods_list = raw_order.get('good_list', [])
    if isinstance(raw_goods_list, list):
        for item in raw_goods_list:
            transformed_item = {
                'order_id': order_id, # FK back to order
                'goods_resource_id': item.get('resource_id'), # FK to goods table (assuming resource_id is the key)
                'goods_spu_id': item.get('spu_id'),
                'sku_id': item.get('sku_id'),
                'goods_name': item.get('goods_name'),
                'sku_spec_description': item.get('goods_spec_desc'),
                'quantity': _safe_to_int(item.get('buy_num')),
                'unit_price': _cents_to_float(item.get('unit_price')),
                'total_price': _cents_to_float(item.get('total_price')), # Price for this line item
                'resource_type': _safe_to_int(item.get('resource_type')),
                'refund_state': _safe_to_int(item.get('refund_state')),
                'ship_state': _safe_to_int(item.get('ship_state')),
            }
            transformed_goods_list.append(transformed_item)

    # Handle potentially missing or empty promoter info
    promoter_user_id = promoter_info.get('user_id') # Get user_id, could be None or empty
    promoter_nickname = promoter_info.get('nickname')

    return {
        # Order Header Info
        'order_id': order_id, # PK
        'user_id': order_info.get('user_id'), # FK to users table
        'created_at': _safe_to_datetime(order_info.get('created_time')),
        'paid_at': _safe_to_datetime(order_info.get('pay_state_time')),
        'updated_at': _safe_to_datetime(order_info.get('update_time')),
        'settled_at': _safe_to_datetime(order_info.get('settle_state_time')),
        'order_state': _safe_to_int(order_info.get('order_state')),
        'pay_state': _safe_to_int(order_info.get('pay_state')),
        'settle_state': _safe_to_int(order_info.get('settle_state')),
        'aftersale_show_state': _safe_to_int(order_info.get('aftersale_show_state')),
        'order_type': _safe_to_int(order_info.get('order_type')),
        'pay_type': _safe_to_int(order_info.get('pay_type')),
        'trade_id': order_info.get('trade_id'),
        'app_id': order_info.get('app_id'),
        
        # Price Info
        'goods_original_total_price': _cents_to_float(order_info.get('goods_original_total_price')), # From order_info
        'total_price': _cents_to_float(price_info.get('total_price')), # From price_info
        'actual_fee': _cents_to_float(order_info.get('actual_fee')), # From order_info, often same as price_info.actual_price
        'discount_amount': _cents_to_float(order_info.get('discount_amount')), # From order_info
        'freight_price': _cents_to_float(price_info.get('freight_price')),
        'total_modified_amount': _cents_to_float(price_info.get('total_modified_amount')),

        # Shipping Info
        'ship_receiver': ship_info.get('receiver'),
        'ship_phone': ship_info.get('phone'),
        'ship_province': ship_info.get('province'),
        'ship_city': ship_info.get('city'),
        'ship_county': ship_info.get('county'),
        'ship_detail': ship_info.get('detail'),
        'ship_company': ship_info.get('company'),
        'ship_express_id': ship_info.get('express_id'),
        'shipped_at': _safe_to_datetime(ship_info.get('ship_time')),
        'ship_confirmed_at': _safe_to_datetime(ship_info.get('confirm_time')),
        
        # Promoter Info
        'promoter_user_id': promoter_user_id if promoter_user_id else None,
        'promoter_nickname': promoter_nickname if promoter_nickname else None,

        # Buyer Comment (from buyer_info, though user_id is the main link)
        'buyer_comment': buyer_info.get('comment'), 
        
        # Order Items (List - for potential storage as JSON or separate table)
        'order_items': transformed_goods_list 
    }

def transform_aftersale(raw_aftersale: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transforms raw aftersale data from Xiaoe API into a structured dictionary."""
    if not raw_aftersale or not raw_aftersale.get('aftersale_id'):
        logger.warning("Skipping aftersale transformation due to missing data or aftersale_id.")
        return None
        
    aftersale_id = raw_aftersale.get('aftersale_id')

    # Transform goods list within the aftersale record
    transformed_goods_list = []
    raw_goods_list = raw_aftersale.get('goods_list', [])
    if isinstance(raw_goods_list, list):
         for item in raw_goods_list:
             transformed_item = {
                 'aftersale_id': aftersale_id, # FK back to aftersale
                 # Assuming goods_name/img_url/sku_info are enough, or need a goods_id? 
                 # The list doesn't seem to contain resource_id directly.
                 'goods_name': item.get('goods_name'),
                 'sku_info': item.get('sku_info'),
                 'quantity': _safe_to_int(item.get('buy_num')),
                 'price': _cents_to_float(item.get('goods_price')),
                 'goods_tag': item.get('goods_tag'),
                 'img_url': item.get('img_url'),
             }
             transformed_goods_list.append(transformed_item)

    return {
        'aftersale_id': aftersale_id, # PK
        'order_id': raw_aftersale.get('order_id'), # FK to orders table
        # user_id is not directly in the aftersale record from list API, need to join via order_id
        'state': _safe_to_int(raw_aftersale.get('state')),
        'state_description': raw_aftersale.get('state_str'),
        'sale_type': _safe_to_int(raw_aftersale.get('sale_type')),
        'sale_type_name': raw_aftersale.get('sale_type_name'),
        'apply_refund_amount': _cents_to_float(raw_aftersale.get('apply_refund_money')),
        'actual_refund_amount': _cents_to_float(raw_aftersale.get('refund_money')),
        'reason': raw_aftersale.get('reason'),
        'buyer_remark': raw_aftersale.get('remark'),
        'merchant_remark': raw_aftersale.get('merchant_remark'),
        'state_reason': raw_aftersale.get('state_reason'),
        'created_at': _safe_to_datetime(raw_aftersale.get('created_at')),
        'updated_at': _safe_to_datetime(raw_aftersale.get('updated_at')),
        'invalid_at': _safe_to_datetime(raw_aftersale.get('invalid_time')), # Note: sample showed '1970-01-01...' which becomes None
        'state_invalid_at': _safe_to_datetime(raw_aftersale.get('state_invalid_time')),
        
        # Info about the first (?) good involved in the aftersale (might be less reliable than goods_list)
        'main_goods_name': raw_aftersale.get('goods_name'),
        'main_sku_id': raw_aftersale.get('sku_id'),
        'main_sku_info': raw_aftersale.get('sku_info'),
        
        # Original order amount (useful context)
        'order_actual_fee': _cents_to_float(raw_aftersale.get('actual_fee')),
        
        # Aftersale Items (List)
        'aftersale_items': transformed_goods_list
    }

def transform_goods(raw_goods: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transforms raw goods data (from goods list API) into a structured dictionary."""
    resource_id = raw_goods.get('resource_id')
    if not raw_goods or not resource_id:
        logger.warning("Skipping goods transformation due to missing data or resource_id.")
        return None

    # Extract sell_num from extend array
    sell_num = None
    extend_list = raw_goods.get('extend', [])
    if isinstance(extend_list, list) and len(extend_list) > 0 and isinstance(extend_list[0], dict):
        sell_num = _safe_to_int(extend_list[0].get('sell_num'))

    return {
        'goods_resource_id': resource_id, # PK (using resource_id as it seems unique across types)
        'spu_id': raw_goods.get('spu_id'), # Often same as resource_id for single items
        'goods_internal_id': _safe_to_int(raw_goods.get('id')), # Xiaoe internal ID
        'goods_name': raw_goods.get('goods_name'),
        'resource_type': _safe_to_int(raw_goods.get('resource_type')),
        'spu_type': raw_goods.get('spu_type'), # e.g., VDO, ENT, VCP
        'goods_category_id': raw_goods.get('goods_category_id'),
        'goods_tag': raw_goods.get('goods_tag'),
        'sell_type': _safe_to_int(raw_goods.get('sell_type')), # 1-独立, 2-关联
        'sale_status': _safe_to_int(raw_goods.get('sale_status')), # 0-下架, 1-上架, 2-待上架
        'price_low': _cents_to_float(raw_goods.get('price_low')),
        'price_high': _cents_to_float(raw_goods.get('price_high')),
        'price_line': _cents_to_float(raw_goods.get('price_line')),
        'created_at': _safe_to_datetime(raw_goods.get('created_at')),
        'updated_at': _safe_to_datetime(raw_goods.get('updated_at')),
        'sale_at': _safe_to_datetime(raw_goods.get('sale_at')),
        'is_deleted': True if _safe_to_int(raw_goods.get('is_deleted')) == 1 else False,
        'is_display': True if _safe_to_int(raw_goods.get('is_display')) == 1 else False,
        'is_stop_sell': True if _safe_to_int(raw_goods.get('is_stop_sell')) == 1 else False,
        'is_forbid': True if _safe_to_int(raw_goods.get('is_forbid')) == 1 else False,
        'visit_count': _safe_to_int(raw_goods.get('visit_num')),
        'appraise_count': _safe_to_int(raw_goods.get('appraise_num')),
        'sell_count': sell_num, # Extracted from extend
        'stock_deduct_mode': _safe_to_int(raw_goods.get('stock_deduct_mode')), # 0-付款减, 1-拍下减
        'limit_purchase': _safe_to_int(raw_goods.get('limit_purchase')),
        'has_distribute': True if _safe_to_int(raw_goods.get('has_distribute')) == 1 else False,
        'freight': _cents_to_float(raw_goods.get('freight')),
        'freight_template_id': raw_goods.get('freight_template_id'), # Could be int or string? Keep as is for now
        'img_url': raw_goods.get('img_url_compressed'), # Use compressed URL
        'main_img_urls': raw_goods.get('goods_img') # List of URLs
        # Add other fields from the sample if needed (e.g., is_best, is_hot, sell_mode...)
    } 
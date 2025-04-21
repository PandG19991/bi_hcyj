"""
小鹅通API数据转换工具
"""

def transform_order(order_data):
    """
    转换订单数据格式
    
    Args:
        order_data: 小鹅通API返回的订单数据
        
    Returns:
        dict: 标准化后的订单数据
    """
    return {
        'order_id': order_data.get('order_id', ''),
        'user_id': order_data.get('user_id', ''),
        'price': float(order_data.get('price', 0)) / 100,  # 分转元
        'coupon_price': float(order_data.get('coupon_price', 0)) / 100,
        'refund_money': float(order_data.get('refund_money', 0)) / 100,
        'order_state': order_data.get('order_state', 0),
        'order_state_text': order_data.get('order_state_text', ''),
        'resource_type': order_data.get('resource_type', 0),
        'resource_type_text': order_data.get('resource_type_text', ''),
        'ship_state': order_data.get('ship_state', 0),
        'ship_state_text': order_data.get('ship_state_text', ''),
        'pay_way': order_data.get('pay_way', 0),
        'client_type': order_data.get('client_type', 0),
        'collection_way': order_data.get('collection_way', 0),
        'after_sales_state': order_data.get('after_sales_state', 0),
        'team_buy_state': order_data.get('team_buy_state', 0),
        'sales_state': order_data.get('sales_state', 0),
        'created_at': order_data.get('created_at', ''),
        'pay_time': order_data.get('pay_time', '')
    }

def transform_order_items(order_data):
    """
    从订单数据中提取订单商品数据
    
    Args:
        order_data: 小鹅通API返回的订单数据
        
    Returns:
        list: 标准化后的订单商品数据列表
    """
    order_id = order_data.get('order_id', '')
    resource_list = order_data.get('resource_list', [])
    
    items = []
    for resource in resource_list:
        item = {
            'order_id': order_id,
            'product_id': resource.get('resource_id', ''),
            'product_name': resource.get('title', ''),
            'quantity': resource.get('num', 1),
            'price': float(resource.get('price', 0)) / 100
        }
        items.append(item)
    
    return items

def transform_user(user_data):
    """
    转换用户数据格式
    
    Args:
        user_data: 小鹅通API返回的用户数据
        
    Returns:
        dict: 标准化后的用户数据
    """
    return {
        'user_id': user_data.get('user_id', ''),
        'nickname': user_data.get('nickname', ''),
        'avatar': user_data.get('avatar', ''),
        'mobile': user_data.get('mobile', ''),
        'email': user_data.get('email', ''),
        'gender': user_data.get('gender', 0),
        'birthday': user_data.get('birthday', ''),
        'province': user_data.get('province', ''),
        'city': user_data.get('city', ''),
        'register_time': user_data.get('register_time', '')
    }

def transform_product(product_data):
    """
    转换商品数据格式
    
    Args:
        product_data: 小鹅通API返回的商品数据
        
    Returns:
        dict: 标准化后的商品数据
    """
    return {
        'product_id': product_data.get('goods_id', ''),
        'title': product_data.get('title', ''),
        'sub_title': product_data.get('sub_title', ''),
        'price': float(product_data.get('price', 0)) / 100,
        'original_price': float(product_data.get('original_price', 0)) / 100,
        'type': product_data.get('type', 0),
        'cover_img': product_data.get('cover_img', ''),
        'status': product_data.get('status', 0),
        'created_at': product_data.get('created_at', '')
    } 
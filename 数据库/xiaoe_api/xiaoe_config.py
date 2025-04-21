"""
小鹅通API配置和常量定义
"""

# API凭证配置
XIAOE_CONFIG = {
    'app_id': 'app0vuxiwxw3082',  # 替换为你的AppID
    'client_id': 'xop_xxx',        # 替换为你的ClientID
    'client_secret': 'cs_xxx',     # 替换为你的ClientSecret
    'token_file': 'access_token.json',  # token存储文件
    'base_url': 'https://api.xiaoe-tech.com'  # API基础URL
}

# API接口路径
XIAOE_API_ENDPOINTS = {
    'token': '/token',
    'orders': '/xe.goods.orders.get/1.0.0',
    'users': '/xe.user.users.get/1.0.0',
    'products': '/xe.goods.items.get/1.0.0',
    'live_rooms': '/xe.goods.live_rooms.get/1.0.0'
}

# 订单状态映射
ORDER_STATUS = {
    0: '待支付',
    1: '支付中',
    2: '支付成功',
    3: '已退款',
    4: '支付失败',
    5: '已失效'
}

# 商品类型映射
PRODUCT_TYPE = {
    1: '直播',
    2: '视频',
    3: '音频',
    4: '图文',
    5: '电子书',
    6: '线下课',
    7: '会员',
    8: '专栏',
    9: '话题',
    10: '社区',
    11: '训练营'
} 
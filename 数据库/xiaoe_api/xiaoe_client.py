"""
小鹅通API客户端实现类
"""
import os
import json
import time
import requests
from loguru import logger

class XiaoeClient:
    def __init__(self, config):
        """
        初始化小鹅通API客户端
        
        Args:
            config: API配置字典
        """
        self.app_id = config['app_id']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.token_file = config['token_file']
        self.base_url = config['base_url']
        self.access_token = None
        self.expires_at = 0
        self.load_token()
    
    def load_token(self):
        """从文件加载token，如果存在且未过期"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    if token_data.get('expires_at', 0) > time.time() + 300:  # 提前5分钟刷新
                        self.access_token = token_data.get('access_token')
                        self.expires_at = token_data.get('expires_at')
                        logger.info(f"已从文件加载token，过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.expires_at))}")
                    else:
                        logger.info("token已过期或即将过期，将重新获取")
            except Exception as e:
                logger.error(f"加载token文件失败: {e}")
    
    def save_token(self):
        """保存token到文件"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump({
                    'access_token': self.access_token,
                    'expires_at': self.expires_at
                }, f)
            logger.info(f"token已保存到文件，过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.expires_at))}")
        except Exception as e:
            logger.error(f"保存token文件失败: {e}")
    
    def get_token(self):
        """
        获取或刷新access_token
        
        Returns:
            str: 访问令牌
        """
        # 如果token有效，直接返回
        if self.access_token and self.expires_at > time.time() + 300:
            return self.access_token
        
        # 否则重新获取token
        try:
            url = f"{self.base_url}/token"
            data = {
                "app_id": self.app_id,
                "client_id": self.client_id,
                "secret_key": self.client_secret,
                "grant_type": "client_credential"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                logger.error(f"获取token失败: {result.get('msg')}")
                return None
            
            self.access_token = result.get('data', {}).get('access_token')
            expires_in = result.get('data', {}).get('expires_in', 7200)
            self.expires_at = time.time() + expires_in
            
            # 保存token
            self.save_token()
            logger.info("成功获取新token")
            return self.access_token
            
        except Exception as e:
            logger.error(f"获取token异常: {e}")
            return None
    
    def api_request(self, endpoint, method='GET', params=None, data=None, retry=3):
        """
        发送API请求
        
        Args:
            endpoint: API端点路径
            method: 请求方法，默认GET
            params: URL参数
            data: 请求体数据
            retry: 重试次数
            
        Returns:
            dict: API响应数据
        """
        if params is None:
            params = {}
        
        # 获取token
        token = self.get_token()
        if not token:
            logger.error("无法获取有效token")
            return {'code': -1, 'msg': '无法获取有效token'}
        
        # 构建请求
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # 添加公共参数
        if 'app_id' not in params:
            params['app_id'] = self.app_id
        
        # 重试机制
        for attempt in range(retry):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, params=params, headers=headers)
                else:
                    response = requests.post(url, params=params, json=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 检查token是否过期
                if result.get('code') == 401:
                    logger.warning("token已过期，尝试刷新")
                    self.access_token = None
                    token = self.get_token()
                    headers['Authorization'] = f'Bearer {token}'
                    continue
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常 (尝试 {attempt+1}/{retry}): {e}")
                if attempt == retry - 1:
                    return {'code': -1, 'msg': f'API请求异常: {e}'}
                time.sleep(1)  # 等待1秒后重试
    
    def get_orders(self, page=1, page_size=20, start_time=None, end_time=None, order_state=None):
        """
        获取订单列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页条数，最大100
            start_time: 开始时间，格式：YYYY-MM-DD HH:MM:SS
            end_time: 结束时间，格式：YYYY-MM-DD HH:MM:SS
            order_state: 订单状态，0待支付，2支付成功，3已退款
            
        Returns:
            dict: 订单列表响应
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        
        if start_time:
            params['start_time'] = start_time
        
        if end_time:
            params['end_time'] = end_time
        
        if order_state is not None:
            params['order_state'] = order_state
        
        from xiaoe_config import XIAOE_API_ENDPOINTS
        return self.api_request(XIAOE_API_ENDPOINTS['orders'], params=params)
    
    def get_user_info(self, user_id):
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户信息响应
        """
        params = {
            'user_id': user_id
        }
        
        from xiaoe_config import XIAOE_API_ENDPOINTS
        return self.api_request(XIAOE_API_ENDPOINTS['users'], params=params)
    
    def get_product_info(self, product_id):
        """
        获取商品信息
        
        Args:
            product_id: 商品ID
            
        Returns:
            dict: 商品信息响应
        """
        params = {
            'goods_id': product_id
        }
        
        from xiaoe_config import XIAOE_API_ENDPOINTS
        return self.api_request(XIAOE_API_ENDPOINTS['products'], params=params)
    
    def get_live_rooms(self, page=1, page_size=20, status=None):
        """
        获取直播间列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页条数
            status: 直播状态，1未开始，2直播中，3已结束
            
        Returns:
            dict: 直播间列表响应
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        
        if status is not None:
            params['status'] = status
        
        from xiaoe_config import XIAOE_API_ENDPOINTS
        return self.api_request(XIAOE_API_ENDPOINTS['live_rooms'], params=params) 
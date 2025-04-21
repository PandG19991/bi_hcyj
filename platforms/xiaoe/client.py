import time
import requests
import json
from typing import Dict, Any, Optional

# 导入项目配置、日志和重试装饰器
from config.config import settings
from utils.logger import logger
from utils.retry import retry

# 修改基础 URL
XIAOE_BASE_URL = "https://api.xiaoe-tech.com/"

# 修改 API 端点格式
XIAOE_API_ENDPOINTS = {
    'token': 'token', # Token 获取路径比较特殊，单独处理
    'orders': 'xe.ecommerce.order.order.list/1.0.0', # <-- 使用用户指定的地址
    'users': 'xe.user.info.get/1.0.0',   # 获取单个用户信息
    'products': 'xe.goods.info.get/1.0.0', # 获取单个商品信息
    # 'live_rooms': 'xe.live.list.get/1.0.0' # 直播列表 (如果需要)
}

class XiaoeAuthError(Exception):
    """小鹅通认证或权限错误。"""
    pass

class XiaoeRequestError(Exception):
    """小鹅通 API 请求错误。"""
    pass

class XiaoeClient:
    """小鹅通 API 客户端实现类 (根据官方示例调整)。"""

    def __init__(self):
        """初始化客户端，从 settings 加载配置。"""
        self.app_id = settings.XIAOE_APP_ID
        self.client_id = settings.XIAOE_CLIENT_ID
        self.client_secret = settings.XIAOE_SECRET_KEY
        self.base_url = XIAOE_BASE_URL
        self.access_token: Optional[str] = None
        self.expires_at: int = 0
        logger.info("XiaoeClient initialized.")

    def _get_access_token(self) -> Optional[str]:
        """内部方法：获取或刷新 access_token (根据官方示例调整)。"""
        if self.access_token and self.expires_at > time.time() + 300:
            logger.debug("Using cached Xiaoe access token.")
            return self.access_token

        logger.info("Attempting to get new Xiaoe access token...")
        # Token URL 直接拼接
        token_url = f"{self.base_url}{XIAOE_API_ENDPOINTS['token']}"
        payload = {
            "app_id": self.app_id,
            "client_id": self.client_id,
            "secret_key": self.client_secret,
            "grant_type": "client_credential"
        }
        headers = {"Content-Type": "application/json"}

        try:
            # 官方示例使用 GET + data，我们遵循它
            logger.debug(f"Requesting token from {token_url} with payload: {payload}")
            response = requests.get(token_url, headers=headers, data=json.dumps(payload), timeout=15)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                data = result.get("data", {})
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)
                self.expires_at = time.time() + expires_in
                logger.info(f"Successfully obtained Xiaoe access token. Expires around: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.expires_at))}")
                return self.access_token
            else:
                error_msg = f"Failed to get Xiaoe token. Code: {result.get('code')}, Msg: {result.get('msg', 'Unknown error')}"
                logger.error(error_msg)
                if result.get('code') in [40001, 40002, 40003]:
                     raise XiaoeAuthError(error_msg)
                else:
                    raise XiaoeRequestError(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Xiaoe token: {e}", exc_info=True)
            raise XiaoeRequestError(f"Network or request error getting token: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting Xiaoe token: {e}", exc_info=True)
            raise XiaoeRequestError(f"Unexpected error getting token: {e}") from e

    @retry(exceptions=(XiaoeRequestError,))
    def _make_request(self, endpoint_key: str, method: str = 'POST', user_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """内部方法：执行 API 请求 (根据官方示例调整)。"""
        token = self._get_access_token()
        if not token:
            logger.critical("Failed to obtain access token before making request.")
            raise XiaoeAuthError("Access token is missing or could not be obtained.")

        api_path = XIAOE_API_ENDPOINTS.get(endpoint_key)
        if not api_path:
            raise ValueError(f"Invalid endpoint key: {endpoint_key}")
        url = f"{self.base_url}{api_path}"

        headers = {
            'Content-Type': 'application/json'
        }

        # 将 token 和业务参数合并到 payload
        payload_dict = user_params.copy() if user_params else {}
        payload_dict["access_token"] = token
        payload_json = json.dumps(payload_dict)

        logger.debug(f"Making Xiaoe API request to {url} with method {method}. Payload: {payload_json}")
        
        # 添加重试逻辑在这里，或者在调用方处理
        # MVP 简化：暂时不加内部重试，依赖外部或手动重跑
        try:
            response = requests.request(method, url, headers=headers, data=payload_json, timeout=30)
            response.raise_for_status() 
            result = response.json()
            response_code = result.get('code')

            if response_code == 0:
                logger.debug(f"Xiaoe API request successful for {endpoint_key}.")
                return result.get('data', {}) # 返回 data 部分
            # Token 过期处理（需要确认错误码）
            elif response_code in [40101, 40102, 40103, 40104, 40105, 40107]: # 假设这些是 token 相关错误
                error_msg = f"Token invalid/expired error (Code: {response_code}, Msg: {result.get('msg')}). Clearing token."
                logger.warning(error_msg)
                self.access_token = None # 清除 token，下次请求会重新获取
                self.expires_at = 0
                raise XiaoeAuthError(error_msg)
            else:
                error_msg = f"Xiaoe API returned error. Endpoint: {endpoint_key}, Code: {response_code}, Msg: {result.get('msg', 'Unknown API error')}"
                logger.error(error_msg)
                raise XiaoeRequestError(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"Xiaoe API request failed (network/http error) for {endpoint_key}: {e}", exc_info=True)
            raise XiaoeRequestError(f"Request failed for endpoint {endpoint_key}: {e}") from e
        except XiaoeAuthError as e: # 重新抛出认证错误
             logger.warning(f"Authentication error during request for {endpoint_key}: {e}")
             raise
        except Exception as e:
            logger.error(f"Unexpected error during Xiaoe API request for {endpoint_key}: {e}", exc_info=True)
            raise XiaoeRequestError(f"Unexpected error for endpoint {endpoint_key}: {e}") from e

    # --- 公开方法，调用 _make_request --- 

    def get_orders(self, page: int = 1, page_size: int = 50, start_time: Optional[str] = None, end_time: Optional[str] = None, order_state: Optional[int] = None) -> Dict[str, Any]:
        """
        获取订单列表 (xe.order.list.get/1.0.2)。
        参数放入 user_params。
        """
        user_params = {
            'page': page,
            'page_size': page_size
        }
        if start_time: user_params['start_time'] = start_time
        if end_time: user_params['end_time'] = end_time
        if order_state is not None: user_params['order_state'] = order_state

        logger.info(f"Fetching orders: page={page}, size={page_size}, start={start_time}, end={end_time}, state={order_state}")
        # API 请求现在总是 POST，参数在 payload 里
        return self._make_request('orders', method='POST', user_params=user_params)

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取单个用户信息 (xe.user.info.get/1.0.0)。
        """
        user_params = {'user_id': user_id}
        logger.info(f"Fetching user info for user_id: {user_id}")
        return self._make_request('users', method='POST', user_params=user_params)

    def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """
        获取单个商品信息 (xe.goods.info.get/1.0.0)。
        """
        user_params = {'goods_id': product_id}
        logger.info(f"Fetching product info for product_id: {product_id}")
        return self._make_request('products', method='POST', user_params=user_params)

    # 可以添加其他需要的 API 方法，例如获取用户列表、商品列表等
    # def get_users(self, ...)
    # def get_products(self, ...)

# --- 使用示例 (可选) ---
# if __name__ == '__main__':
#     # 需要在 config/.env 文件中配置好 XIAOE 相关密钥
#     if not all([settings.XIAOE_APP_ID, settings.XIAOE_CLIENT_ID, settings.XIAOE_SECRET_KEY]):
#         print("错误：请先在 config/.env 文件中配置小鹅通 API 密钥！")
#         exit()
#
#     client = XiaoeClient()
#
#     try:
#         print("\n--- 测试获取订单 ---")
#         # 注意：start_time/end_time 格式要正确
#         # orders_data = client.get_orders(page=1, page_size=5, start_time="2023-01-01 00:00:00", end_time="2023-12-31 23:59:59")
#         orders_data = client.get_orders(page=1, page_size=2)
#         print(json.dumps(orders_data, indent=4, ensure_ascii=False))
#
#         if orders_data and orders_data.get('list'):
#             sample_order = orders_data['list'][0]
#             sample_user_id = sample_order.get('user_id')
#             sample_product_id = None
#             if sample_order.get('resource_list'):
#                 sample_product_id = sample_order['resource_list'][0].get('resource_id')
#
#             if sample_user_id:
#                 print("\n--- 测试获取用户信息 ---")
#                 user_data = client.get_user_info(sample_user_id)
#                 print(json.dumps(user_data, indent=4, ensure_ascii=False))
#
#             if sample_product_id:
#                 print("\n--- 测试获取商品信息 ---")
#                 product_data = client.get_product_info(sample_product_id)
#                 print(json.dumps(product_data, indent=4, ensure_ascii=False))
#
#     except (XiaoeAuthError, XiaoeRequestError, ValueError) as e:
#         print(f"API 请求时发生错误: {e}")
#     except Exception as e:
#         print(f"发生意外错误: {e}") 
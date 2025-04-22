import time
import requests
import json
from typing import Dict, Any, Optional, Generator

# 导入项目配置、日志和重试装饰器
from config.config import settings
from utils.logger import logger
from utils.retry import retry
# 导入新的调试装饰器
from utils.retry import simple_passthrough_decorator

# 修改基础 URL
XIAOE_BASE_URL = "https://api.xiaoe-tech.com/"

# 修改 API 端点格式
XIAOE_API_ENDPOINTS = {
    'token': 'token', # Token 获取路径比较特殊，单独处理
    'orders': '/xe.ecommerce.order.list/1.0.0',
    'users': '/xe.user.list.get/2.0.0',
    'user_detail': '/xe.user.info.get/1.0.0',
    'products': '/xe.goods.list.get/2.0.0',
    'product_detail': '/xe.goods.detail.get/2.0.0',
    'after_sale_orders': '/xe.ecommerce.after_sale.list/1.0.0', # 新增售后列表接口
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
        token_url = f"{self.base_url}{XIAOE_API_ENDPOINTS['token']}"
        payload = {
            "app_id": self.app_id,
            "client_id": self.client_id,
            "secret_key": self.client_secret,
            "grant_type": "client_credential"
        }
        headers = {"Content-Type": "application/json"}

        try:
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

    @retry(exceptions=(XiaoeRequestError,), tries=settings.API_RETRY_TIMES, delay=settings.API_RETRY_DELAY_SECONDS)
    def _make_request(self, endpoint_key: str, method: str = 'POST', user_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """内部方法：执行 API 请求 (根据官方示例调整)，包含重试逻辑。"""
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

        payload_dict = user_params.copy() if user_params else {}
        payload_dict["access_token"] = token
        payload_json = json.dumps(payload_dict)

        logger.debug(f"Making Xiaoe API request to {url} with method {method}. Payload: {payload_json[:500]}..." ) # 截断 payload 避免过长日志

        try:
            response = requests.request(method, url, headers=headers, data=payload_json, timeout=30)
            response.raise_for_status()
            result = response.json()
            response_code = result.get('code')

            if response_code == 0:
                logger.debug(f"Xiaoe API request successful for {endpoint_key}.")
                return result.get('data', {}) # 返回 data 部分
            elif response_code in [40101, 40102, 40103, 40104, 40105, 40107]:
                error_msg = f"Token invalid/expired error (Code: {response_code}, Msg: {result.get('msg')}). Clearing token."
                logger.warning(error_msg)
                self.access_token = None
                self.expires_at = 0
                raise XiaoeAuthError(error_msg)
            else:
                error_msg = f"Xiaoe API returned error. Endpoint: {endpoint_key}, Code: {response_code}, Msg: {result.get('msg', 'Unknown API error')}"
                logger.error(error_msg)
                raise XiaoeRequestError(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"Xiaoe API request failed (network/http error) for {endpoint_key}: {e}", exc_info=True)
            raise XiaoeRequestError(f"Request failed for endpoint {endpoint_key}: {e}") from e
        except XiaoeAuthError as e: # 重新抛出认证错误，不被 retry 捕获
             logger.warning(f"Authentication error during request for {endpoint_key}: {e}")
             raise
        except Exception as e: # 捕获其他意外错误
            logger.error(f"Unexpected error during Xiaoe API request for {endpoint_key}: {e}", exc_info=True)
            raise XiaoeRequestError(f"Unexpected error for endpoint {endpoint_key}: {e}") from e

    # --- 公开方法，调用 _make_request --- 

    def get_orders(self, page_size: int = 50, start_time: Optional[str] = None, end_time: Optional[str] = None, order_state: Optional[int] = None, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        获取订单列表 (xe.ecommerce.order.list/1.0.0)，自动处理分页。
        使用生成器返回每一页的原始 API 响应数据 (data 部分)。
        Args:
            page_size: 每页数量 (默认 50, 根据 API 文档调整上限)。
            start_time: 订单创建起始时间 (格式: 'YYYY-MM-DD HH:MM:SS')。
            end_time: 订单创建结束时间 (格式: 'YYYY-MM-DD HH:MM:SS')。
            order_state: 订单状态码。
            **kwargs: 其他 API 支持的过滤参数。
        Yields:
            每一页请求成功后返回的 data 字典。
        """
        page = 1
        total_pages = None
        logger.info(f"Starting paginated fetch for orders: size={page_size}, start={start_time}, end={end_time}, state={order_state}, filters={kwargs}")
        while True:
            if total_pages is None or page <= total_pages:
                 logger.info(f"Fetching orders page {page}" + (f"/{total_pages}" if total_pages else ""))
            else:
                 logger.info(f"Reached estimated end of pages ({page-1}/{total_pages}). Stopping.")
                 break
            user_params = {
                "page_index": page,
                "page_size": page_size,
                "begin_time": start_time,
                "end_time": end_time,
                "order_state": order_state,
                **kwargs
            }
            user_params = {k: v for k, v in user_params.items() if v is not None}
            try:
                response_data = self._make_request('orders', method='POST', user_params=user_params)
                current_page_data = response_data.get('list', [])
                total_count = response_data.get('total_count')
                if total_count is not None and total_pages is None:
                    total_pages = (int(total_count) + page_size - 1) // page_size
                    logger.info(f"Total records estimated: {total_count}, total pages: {total_pages}")
                if current_page_data:
                    logger.debug(f"Yielding data for orders page {page}, items: {len(current_page_data)}")
                    yield response_data
                else:
                    logger.info(f"No more data found for orders on page {page}. Stopping pagination.")
                    break
                if total_pages is not None and page >= total_pages:
                    logger.info(f"Reached last page ({page}/{total_pages}). Stopping.")
                    break
                page += 1
                time.sleep(0.1)
            except XiaoeAuthError as e:
                logger.error(f"Authentication error during fetching orders page {page}: {e}. Stopping pagination.", exc_info=True)
                raise
            except XiaoeRequestError as e:
                logger.error(f"Request error during fetching orders page {page} after retries: {e}. Stopping pagination.", exc_info=True)
                break
            except Exception as e:
                logger.error(f"Unexpected error during fetching orders page {page}: {e}. Stopping pagination.", exc_info=True)
                break
        logger.info("Finished paginated fetch for orders.")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取单个用户信息 (xe.user.info.get/1.0.0)。
        """
        user_params = {'user_id': user_id}
        logger.info(f"Fetching user info for user_id: {user_id}")
        return self._make_request('user_detail', method='POST', user_params=user_params)

    def get_users(self, page_size: int = 50, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        获取用户列表 (xe.user.list.get/2.0.0)，自动处理分页。
        Args:
            page_size: 每页数量 (默认 50)。
            **kwargs: 其他 API 支持的过滤参数。
        Yields:
            每一页请求成功后返回的 data 字典。
        """
        page = 1
        total_pages = None
        logger.info(f"Starting paginated fetch for users: size={page_size}, filters={kwargs}")
        while True:
            if total_pages is None or page <= total_pages:
                 logger.info(f"Fetching users page {page}" + (f"/{total_pages}" if total_pages else ""))
            else:
                 logger.info(f"Reached estimated end of pages ({page-1}/{total_pages}). Stopping.")
                 break
            user_params = {"page_index": page, "page_size": page_size, **kwargs}
            user_params = {k: v for k, v in user_params.items() if v is not None}
            try:
                response_data = self._make_request('users', method='POST', user_params=user_params)
                current_page_data = response_data.get('list', [])
                total_count = response_data.get('total_count')
                if total_count is not None and total_pages is None:
                    total_pages = (int(total_count) + page_size - 1) // page_size
                    logger.info(f"Total records estimated: {total_count}, total pages: {total_pages}")
                if current_page_data:
                    logger.debug(f"Yielding data for users page {page}, items: {len(current_page_data)}")
                    yield response_data
                else:
                    logger.info(f"No more data found for users on page {page}. Stopping pagination.")
                    break
                if total_pages is not None and page >= total_pages:
                    logger.info(f"Reached last page ({page}/{total_pages}). Stopping.")
                    break
                page += 1
                time.sleep(0.1)
            except XiaoeAuthError as e:
                logger.error(f"Authentication error during fetching users page {page}: {e}. Stopping pagination.", exc_info=True)
                raise
            except XiaoeRequestError as e:
                logger.error(f"Request error during fetching users page {page} after retries: {e}. Stopping pagination.", exc_info=True)
                break
            except Exception as e:
                logger.error(f"Unexpected error during fetching users page {page}: {e}. Stopping pagination.", exc_info=True)
                break
        logger.info("Finished paginated fetch for users.")

    def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """
        获取单个商品信息 (xe.goods.detail.get/2.0.0)。
        """
        user_params = {'goods_id': product_id}
        logger.info(f"Fetching product info for product_id: {product_id}")
        return self._make_request('product_detail', method='POST', user_params=user_params)

    def get_products(self, page_size: int = 50, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        获取商品列表 (xe.goods.list.get/2.0.0)，自动处理分页。
        Args:
            page_size: 每页数量 (默认 50)。
            **kwargs: 其他 API 支持的过滤参数。
        Yields:
            每一页请求成功后返回的 data 字典。
        """
        page = 1
        total_pages = None
        logger.info(f"Starting paginated fetch for products: size={page_size}, filters={kwargs}")
        while True:
            if total_pages is None or page <= total_pages:
                 logger.info(f"Fetching products page {page}" + (f"/{total_pages}" if total_pages else ""))
            else:
                 logger.info(f"Reached estimated end of pages ({page-1}/{total_pages}). Stopping.")
                 break
            user_params = {"page_index": page, "page_size": page_size, **kwargs}
            user_params = {k: v for k, v in user_params.items() if v is not None}
            try:
                response_data = self._make_request('products', method='POST', user_params=user_params)
                current_page_data = response_data.get('list', [])
                total_count = response_data.get('total_count')
                if total_count is not None and total_pages is None:
                    total_pages = (int(total_count) + page_size - 1) // page_size
                    logger.info(f"Total records estimated: {total_count}, total pages: {total_pages}")
                if current_page_data:
                    logger.debug(f"Yielding data for products page {page}, items: {len(current_page_data)}")
                    yield response_data
                else:
                    logger.info(f"No more data found for products on page {page}. Stopping pagination.")
                    break
                if total_pages is not None and page >= total_pages:
                    logger.info(f"Reached last page ({page}/{total_pages}). Stopping.")
                    break
                page += 1
                time.sleep(0.1)
            except XiaoeAuthError as e:
                logger.error(f"Authentication error during fetching products page {page}: {e}. Stopping pagination.", exc_info=True)
                raise
            except XiaoeRequestError as e:
                logger.error(f"Request error during fetching products page {page} after retries: {e}. Stopping pagination.", exc_info=True)
                break
            except Exception as e:
                logger.error(f"Unexpected error during fetching products page {page}: {e}. Stopping pagination.", exc_info=True)
                break
        logger.info("Finished paginated fetch for products.")

    def get_after_sale_orders(self, page_size: int = 50, start_time: Optional[str] = None, end_time: Optional[str] = None, date_type: str = 'created_at', **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        获取售后订单列表 (xe.ecommerce.after_sale.list/1.0.0)，自动处理分页。
        Args:
            page_size: 每页数量 (默认 50)。
            start_time: 起始时间。
            end_time: 结束时间。
            date_type: 时间过滤类型 ('created_at' 或 'updated_at')。
            **kwargs: 其他 API 支持的过滤参数。
        Yields:
            每一页请求成功后返回的 data 字典。
        """
        page = 1
        total_pages = None
        logger.info(f"Starting paginated fetch for after-sale orders: size={page_size}, date_type={date_type}, start={start_time}, end={end_time}, filters={kwargs}")
        while True:
            if total_pages is None or page <= total_pages:
                 logger.info(f"Fetching after-sale orders page {page}" + (f"/{total_pages}" if total_pages else ""))
            else:
                 logger.info(f"Reached estimated end of pages ({page-1}/{total_pages}). Stopping.")
                 break
            user_params = {
                "page_index": page,
                "page_size": page_size,
                "date_type": date_type,
                date_type: f"{start_time}||{end_time}" if start_time and end_time else None,
                **kwargs
            }
            user_params = {k: v for k, v in user_params.items() if v is not None}
            try:
                response_data = self._make_request('after_sale_orders', method='POST', user_params=user_params)
                current_page_data = response_data.get('list', [])
                total_count = response_data.get('total_count')
                if total_count is not None and total_pages is None:
                    total_pages = (int(total_count) + page_size - 1) // page_size
                    logger.info(f"Total records estimated: {total_count}, total pages: {total_pages}")
                if current_page_data:
                    logger.debug(f"Yielding data for after-sale orders page {page}, items: {len(current_page_data)}")
                    yield response_data
                else:
                    logger.info(f"No more data found for after-sale orders on page {page}. Stopping pagination.")
                    break
                if total_pages is not None and page >= total_pages:
                    logger.info(f"Reached last page ({page}/{total_pages}). Stopping.")
                    break
                page += 1
                time.sleep(0.1)
            except XiaoeAuthError as e:
                logger.error(f"Authentication error during fetching after-sale orders page {page}: {e}. Stopping pagination.", exc_info=True)
                raise
            except XiaoeRequestError as e:
                logger.error(f"Request error during fetching after-sale orders page {page} after retries: {e}. Stopping pagination.", exc_info=True)
                break
            except Exception as e:
                logger.error(f"Unexpected error during fetching after-sale orders page {page}: {e}. Stopping pagination.", exc_info=True)
                break
        logger.info("Finished paginated fetch for after-sale orders.")

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
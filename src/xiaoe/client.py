# Placeholder for Xiaoe Platform API client

import requests
import time
from typing import Any, Dict, Optional

from src.core.config import settings
from src.core.logger import logger

# Default Xiaoe API Base URL
XIAOE_API_BASE_URL = "https://api.xiaoe-tech.com/"

class XiaoeError(Exception):
    """Custom exception for Xiaoe API errors."""
    def __init__(self, code: int, message: str, details: Optional[Any] = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"Xiaoe API Error - Code: {code}, Message: {message}")

class XiaoeClient:
    """Client for interacting with the XiaoeTech API.
    
    Uses access token obtained via GET /token endpoint.
    Access token is passed in the request body for subsequent API calls.
    """

    def __init__(self, app_id: str = settings.XIAOE_APP_ID, 
                 client_id: str = settings.XIAOE_CLIENT_ID, 
                 secret_key: str = settings.XIAOE_SECRET_KEY,
                 base_url: str = XIAOE_API_BASE_URL):
        
        if not all([app_id, client_id, secret_key]):
            raise ValueError("Xiaoe API credentials (app_id, client_id, secret_key) must be provided.")

        self.app_id = app_id
        self.client_id = client_id
        self.secret_key = secret_key # Still needed for getting the token
        self.base_url = base_url.rstrip('/') + '/' # Ensure trailing slash
        
        self._access_token: Optional[str] = None
        self._token_expires_at: int = 0 # Timestamp when token expires
        self._session = requests.Session()
        # Set default header - note: might not be strictly needed for GET /token
        self._session.headers.update({"Content-Type": "application/json;charset=utf-8"})

    # Removed _generate_signature method as it's not needed for this auth type

    def _get_access_token(self) -> str:
        """Fetch or refresh the access token from Xiaoe API via GET /token."""
        current_time = time.time()
        # Check if token exists and is valid (considering buffer implicitly applied during set)
        if self._access_token and self._token_expires_at > current_time:
            logger.debug("Using cached Xiaoe access token.")
            return self._access_token

        logger.info("Fetching new Xiaoe access token...")
        endpoint = f"{self.base_url}token"
        
        params = {
            "app_id": self.app_id,
            "client_id": self.client_id,
            "secret_key": self.secret_key, 
            "grant_type": "client_credential" 
        }
        
        fetched_token: Optional[str] = None
        
        try:
            response = self._session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                token_data = data.get("data", {})
                new_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 7200)
                
                if not new_token:
                     raise XiaoeError(-1, "Access token not found in successful response data.", data)
                
                self._access_token = new_token
                # Apply buffer when SETTING the expiry time
                self._token_expires_at = current_time + expires_in - 300 
                fetched_token = new_token
                
                logger.info("Successfully obtained new Xiaoe access token.")
            else:
                error_code = data.get("code", -1)
                error_message = data.get("message", "Unknown error fetching token")
                logger.error(f"Failed to get access token. Code: {error_code}, Message: {error_message}, Params: {params}")
                raise XiaoeError(error_code, error_message, data)

        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error while fetching access token: {e}")
            raise XiaoeError(-2, f"Network error: {e}") from e 
        except XiaoeError:
             raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching the access token: {e}")
            raise XiaoeError(-3, f"Unexpected error: {e}") from e 

        if fetched_token:
            return fetched_token
        else:
            raise XiaoeError(-4, "Token fetch attempt completed without obtaining a token.")

    def _make_request(self, method: str, api_path: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an authenticated request to the Xiaoe API (token in body)."""
        token = self._get_access_token()
        url = f"{self.base_url.rstrip('/')}/{api_path.lstrip('/')}"
        
        # Prepare request body (ensure data is a dict)
        request_data = data.copy() if data else {}
        request_data['access_token'] = token # Add token to the JSON body

        # Headers might still be needed, keep the default content-type
        headers = self._session.headers 

        try:
            response = self._session.request(
                method=method.upper(), 
                url=url, 
                params=params, # URL parameters (usually for GET)
                json=request_data, # Request body (POST/PUT)
                headers=headers,
                timeout=30 # Longer timeout for data requests
            )
            response.raise_for_status()
            result = response.json()

            # Check for API-level errors (assuming code 0 is success)
            # Some APIs might return code 0 but have errors inside 'data', handle as needed.
            if result.get("code", 0) != 0:
                error_code = result.get("code", -1)
                error_message = result.get("message", "Unknown API error")
                logger.warning(f"Xiaoe API returned error. URL: {url}, Code: {error_code}, Message: {error_message}, Payload: {request_data}")
                raise XiaoeError(error_code, error_message, result)
            
            # Return only the 'data' part if it exists and code is 0
            # If 'data' doesn't exist but code is 0, return the whole result
            return result.get("data", result)

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during API request to {url}: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                error_code = error_data.get("code", e.response.status_code)
                error_message = error_data.get("message", e.response.text)
                raise XiaoeError(error_code, error_message, error_data) from e
            except ValueError:
                raise XiaoeError(e.response.status_code, e.response.text) from e
        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error during API request to {url}: {e}")
            raise XiaoeError(-2, f"Network error: {e}")
        except XiaoeError: # Re-raise specific Xiaoe errors
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred during API request to {url}: {e}")
            raise XiaoeError(-3, f"Unexpected error: {e}")

    # --- Example API Method Implementations --- 

    def get_users_list(self, page_size: int = 50, es_skip: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Fetch a list of users using cursor-based pagination (API: xe.user.batch.get/2.0.0).

        Args:
            page_size: The number of users per page (max 50).
            es_skip: The es_skip object from the previous page's last item for pagination.
                     Pass None or omit for the first page.
            **kwargs: Additional filter parameters as defined in the API documentation 
                      (e.g., phone, nickname, tag_id, user_created_start, etc.).

        Returns:
            A dictionary containing the list of users and pagination info.
            Example: {'list': [...], 'total': 163}
        
        Raises:
            XiaoeError: If the API request fails.
        """
        api_path = "xe.user.batch.get/2.0.0" # Confirmed endpoint
        
        if not 1 <= page_size <= 50:
             raise ValueError("page_size must be between 1 and 50")

        payload = {k: v for k, v in kwargs.items() if v is not None and v != ''} 
        payload["page_size"] = page_size
        if es_skip:
            payload["es_skip"] = es_skip

        logger.debug(f"Fetching user list with page_size={page_size}, es_skip={es_skip}, filters={kwargs}")
        return self._make_request("POST", api_path, data=payload) # POST confirmed

    def get_order_list(self, search_type: int, start_time: str, end_time: str, page: int = 1, page_size: int = 50, **kwargs) -> Dict[str, Any]:
        """Fetch a list of orders (API: xe.ecommerce.order.list/1.0.0).

        Args:
            search_type: Search time type (1: created_time, 2: pay_time, 3: update_time, 4: aftersale_update_time).
            start_time: Start time string (YYYY-MM-DD HH:mm:ss).
            end_time: End time string (YYYY-MM-DD HH:mm:ss).
            page: Page number to fetch (starts from 1).
            page_size: Number of orders per page (max 50).
            **kwargs: Additional filter parameters (e.g., order_state, user_id, phone_number, etc.).

        Returns:
            A dictionary containing the list of orders and pagination info.
        
        Raises:
            XiaoeError: If the API request fails.
        """
        api_path = "xe.ecommerce.order.list/1.0.0" # Confirmed endpoint
        
        if not 1 <= page_size <= 50:
            raise ValueError("page_size must be between 1 and 50")

        # Parameters are top-level, alongside access_token
        payload = {k: v for k, v in kwargs.items() if v is not None and v != ''} 
        payload["search_type"] = search_type
        payload["start_time"] = start_time
        payload["end_time"] = end_time
        payload["page"] = page
        payload["page_size"] = page_size

        logger.debug(f"Fetching order list page {page} with size {page_size}, filters={kwargs}")
        return self._make_request("POST", api_path, data=payload) # POST confirmed

    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details (API: xe.ecommerce.order.detail/1.0.0).
        
        Args:
            order_id: The ID of the order to fetch.

        Returns:
            A dictionary containing the order details.

        Raises:
            XiaoeError: If the API request fails.
        """
        api_path = "xe.ecommerce.order.detail/1.0.0" # Confirmed endpoint
        payload = {"order_id": order_id} # Parameter is top-level
        logger.debug(f"Fetching order details for order_id: {order_id}")
        return self._make_request("POST", api_path, data=payload) # POST confirmed

    def get_aftersale_list(self, page_index: int = 1, page_size: int = 50, **kwargs) -> Dict[str, Any]:
        """Fetch a list of aftersale orders (API: xe.ecommerce.after_sale.list/1.0.0).

        Args:
            page_index: Page number to fetch (starts from 1).
            page_size: Number of records per page (max 50).
            **kwargs: Additional filter parameters (e.g., aftersale_id, state, date_type, created_at).
                      All parameters are passed as top-level keys in the request payload.

        Returns:
            A dictionary containing the list of aftersale orders and pagination info.
            Example: {'list': [...], 'row_count': 37}
        
        Raises:
            XiaoeError: If the API request fails.
        """
        api_path = "xe.ecommerce.after_sale.list/1.0.0" # Corrected path based on new doc
        
        if not 1 <= page_size <= 50:
            raise ValueError("page_size must be between 1 and 50")

        # Parameters are top-level, no nesting under "data"
        payload = {k: v for k, v in kwargs.items() if v is not None and v != ''} 
        payload["page_index"] = page_index
        payload["page_size"] = page_size
        
        # Removed nesting: payload = {"data": filter_data}

        logger.debug(f"Fetching aftersale list page {page_index} with size {page_size}, filters={kwargs}")
        # Pass the flat payload directly
        return self._make_request("POST", api_path, data=payload) # POST confirmed

    def get_aftersale_details(self, aftersale_id: str, user_id: Optional[str] = None, order_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch details of a specific aftersale order (API: xe.aftersale.detail/1.0.0).

        Args:
            aftersale_id: The ID of the aftersale order.
            user_id: Optional user ID for permission check.
            order_id: Optional parent order ID for permission check.

        Returns:
            A dictionary containing the detailed aftersale order information.

        Raises:
            XiaoeError: If the API request fails.
        """
        api_path = "xe.aftersale.detail/1.0.0" # Confirmed endpoint
        
        payload = {"aftersale_id": aftersale_id}
        if user_id:
            payload["user_id"] = user_id
        if order_id:
            payload["order_id"] = order_id

        # Parameters are top-level, alongside access_token
        logger.debug(f"Fetching aftersale details for aftersale_id: {aftersale_id}")
        return self._make_request("POST", api_path, data=payload) # POST confirmed

    def get_user_info_batch(self, user_ids: list[str]) -> Dict[str, Any]:
        """Fetch user info for a batch of user IDs (API: xe.user.info.batch.get/1.0.0)."""
        api_path = "xe.user.info.batch.get/1.0.0" # Confirmed endpoint
        if not user_ids:
            raise ValueError("user_ids list cannot be empty.")
        if len(user_ids) > 100:
            logger.warning("Batch user info request contains > 100 user_ids, API might reject.")
        
        # Parameter user_ids is top-level, alongside access_token
        payload = {"user_ids": user_ids}
        logger.debug(f"Fetching batch user info for {len(user_ids)} users.")
        return self._make_request("POST", api_path, data=payload) # POST confirmed 

    # Renamed from get_goods_relations to reflect the actual API called
    def get_goods_list(self, page: int = 1, page_size: int = 10, **kwargs) -> Dict[str, Any]:
        """Fetch a list of goods (products) (API: xe.goods.list.get/4.0.0).

        Corresponds to the "查询商品列表2.0" API.

        Args:
            page: Page number to fetch (starts from 1).
            page_size: Number of goods per page (default 10, max 100).
            **kwargs: Additional filter parameters as defined in the API documentation 
                      (e.g., goods_name, resource_type, sale_status, etc.).

        Returns:
            A dictionary containing the list of goods and pagination info.
            Example: {'current_page': 1, 'list': [...], 'total': 46598}

        Raises:
            XiaoeError: If the API request fails.
            ValueError: If page_size is invalid.
        """
        # Updated API path based on docs/xiaoe_API/get_goods_relations.md
        api_path = "xe.goods.list.get/4.0.0" 

        # API doc says max 100, default 10
        if not 1 <= page_size <= 100:
             raise ValueError("page_size must be between 1 and 100")

        # Parameters are top-level, alongside access_token
        payload = {k: v for k, v in kwargs.items() if v is not None and v != ''} 
        payload["page"] = page # Use 'page' instead of 'page_index'
        payload["page_size"] = page_size

        logger.debug(f"Fetching goods list page {page} with size {page_size}, filters={kwargs}")
        return self._make_request("POST", api_path, data=payload) # POST confirmed 

    def get_user_orders(self, user_id: str, page_index: int = 1, page_size: int = 10, **kwargs) -> Dict[str, Any]:
        """Fetch orders for a specific user (API: xe.get.user.orders/1.0.0).

        Args:
            user_id: The ID of the user whose orders are to be fetched.
            page_index: Page number to fetch (starts from 1).
            page_size: Number of records per page (default 10, max 50).
            **kwargs: Additional filter parameters nested under 'data' (e.g., order_id, 
                      product_id, begin_time, end_time, order_state, payment_type, 
                      resource_type, client_type, order_by).

        Returns:
            A dictionary containing the user's order list and pagination info.
            Example: {'total': 30, 'list': [...]} 

        Raises:
            XiaoeError: If the API request fails.
        """
        api_path = "xe.get.user.orders/1.0.0" # Confirmed endpoint

        if not 1 <= page_size <= 50:
            raise ValueError("page_size must be between 1 and 50")

        # Filters and pagination need to be nested under a "data" key
        filter_data = {k: v for k, v in kwargs.items() if v is not None and v != ''} 
        filter_data["page_index"] = page_index
        filter_data["page_size"] = page_size
        
        # user_id is top-level, data contains filters/pagination
        payload = {
            "user_id": user_id,
            "data": filter_data
        }

        logger.debug(f"Fetching orders for user {user_id}, page {page_index}, size {page_size}, filters={kwargs}")
        return self._make_request("POST", api_path, data=payload) # POST confirmed 
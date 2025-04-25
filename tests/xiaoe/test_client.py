import pytest
import time
import requests
from unittest.mock import patch, MagicMock

from src.xiaoe.client import XiaoeClient, XiaoeError, XIAOE_API_BASE_URL
from src.core.config import Settings # Import Settings to potentially mock it

# Removed old constants TEST_APP_ID, TEST_CLIENT_ID, TEST_SECRET_KEY, TEST_BASE_URL

# Dummy credentials for testing
MOCK_APP_ID = "test_app_id"
MOCK_CLIENT_ID = "test_client_id"
MOCK_SECRET_KEY = "test_secret_key"

# Removed mock_settings fixture as it wasn't working reliably
# @pytest.fixture
# def mock_settings(monkeypatch):
#     ...

@pytest.fixture
def client(): # Removed dependency on mock_settings
    """Fixture to create a XiaoeClient instance with MOCK credentials for testing."""
    # Instantiate client directly with mock credentials
    return XiaoeClient(
        app_id=MOCK_APP_ID,
        client_id=MOCK_CLIENT_ID,
        secret_key=MOCK_SECRET_KEY
        # base_url will use the default XIAOE_API_BASE_URL
    )

# --- Test __init__ --- 

def test_client_initialization_success():
    """Test successful initialization with valid credentials."""
    client = XiaoeClient(
        app_id="test_app_id",
        client_id="test_client_id",
        secret_key="test_secret_key"
    )
    assert client.app_id == "test_app_id"
    assert client.client_id == "test_client_id"
    assert client.secret_key == "test_secret_key"
    assert client.base_url == XIAOE_API_BASE_URL # Default ends with /
    assert client._session is not None # Check session is created
    assert client._access_token is None
    assert client._token_expires_at == 0

def test_client_initialization_with_custom_base_url():
    """Test initialization with a custom base URL."""
    custom_url = "http://custom.api.example.com"
    client = XiaoeClient(
        app_id="test_app_id",
        client_id="test_client_id",
        secret_key="test_secret_key",
        base_url=custom_url
    )
    # Check that a trailing slash is added if missing
    assert client.base_url == custom_url + "/"

def test_client_initialization_missing_appid():
    """Test initialization fails if app_id is missing."""
    # Match the actual error message raised by __init__
    match_str = "Xiaoe API credentials .* must be provided"
    with pytest.raises(ValueError, match=match_str):
        XiaoeClient(app_id=None, client_id="test_client_id", secret_key="test_secret_key")
    with pytest.raises(ValueError, match=match_str):
        XiaoeClient(app_id="", client_id="test_client_id", secret_key="test_secret_key")

def test_client_initialization_missing_clientid():
    """Test initialization fails if client_id is missing."""
    # Match the actual error message raised by __init__
    match_str = "Xiaoe API credentials .* must be provided"
    with pytest.raises(ValueError, match=match_str):
        XiaoeClient(app_id="test_app_id", client_id=None, secret_key="test_secret_key")
    with pytest.raises(ValueError, match=match_str):
        XiaoeClient(app_id="test_app_id", client_id="", secret_key="test_secret_key")

def test_client_initialization_missing_secretkey():
    """Test initialization fails if secret_key is missing."""
    # Match the actual error message raised by __init__
    match_str = "Xiaoe API credentials .* must be provided"
    with pytest.raises(ValueError, match=match_str):
        XiaoeClient(app_id="test_app_id", client_id="test_client_id", secret_key=None)
    with pytest.raises(ValueError, match=match_str):
        XiaoeClient(app_id="test_app_id", client_id="test_client_id", secret_key="")

# --- Test _get_access_token --- 

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_success(mock_get, client):
    """Test successful fetching of a new access token."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": 0,
        "msg": "Success",
        "data": {
            "access_token": "new_token_123",
            "expires_in": 7200
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    token = client._get_access_token()

    assert token == "new_token_123"
    assert client._access_token == "new_token_123"
    assert client._token_expires_at > time.time() + 6800 
    assert client._token_expires_at < time.time() + 7200 

    expected_url = f"{XIAOE_API_BASE_URL}token"
    expected_params = {
        "app_id": MOCK_APP_ID, # Now correctly uses mock value via client fixture
        "client_id": MOCK_CLIENT_ID,
        "secret_key": MOCK_SECRET_KEY,
        "grant_type": "client_credential"
    }
    mock_get.assert_called_once_with(expected_url, params=expected_params, timeout=10)

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_cached(mock_get, client):
    """Test that a valid cached token is returned without a new request."""
    cached_token = "cached_token_xyz"
    client._access_token = cached_token
    client._token_expires_at = time.time() + 3600 

    token = client._get_access_token()

    assert token == cached_token
    mock_get.assert_not_called()

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_expired_cache_refreshes(mock_get, client):
    """Test that a new token is fetched if the cached one is (almost) expired."""
    client._access_token = "expired_token_abc"
    client._token_expires_at = time.time() - 60 # Definitely expired

    mock_response = MagicMock()
    new_token_val = "refreshed_token_456"
    mock_response.json.return_value = {
        "code": 0, "data": {"access_token": new_token_val, "expires_in": 7200}
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    token = client._get_access_token()

    assert token == new_token_val
    assert client._access_token == new_token_val
    mock_get.assert_called_once()

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_api_error_code_not_zero(mock_get, client):
    """Test handling API error (code != 0) during token fetch."""
    mock_response = MagicMock()
    error_code = 10001
    error_msg = "Invalid credentials"
    mock_response.json.return_value = {"code": error_code, "message": error_msg}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(XiaoeError) as excinfo:
        client._get_access_token()
    
    assert excinfo.value.code == error_code
    assert error_msg in str(excinfo.value)

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_success_but_no_token_in_data(mock_get, client):
    """Test handling case where API returns success code but no token."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "data": {"expires_in": 7200}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(XiaoeError) as excinfo:
        client._get_access_token()
    
    assert excinfo.value.code == -1
    assert "Access token not found" in str(excinfo.value)

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_network_error(mock_get, client):
    """Test handling network error during token fetch."""
    error_msg = "Connection timed out"
    mock_get.side_effect = requests.exceptions.Timeout(error_msg)

    with pytest.raises(XiaoeError) as excinfo:
        client._get_access_token()
    
    assert excinfo.value.code == -2
    assert "Network error" in str(excinfo.value)
    assert error_msg in str(excinfo.value)

@patch('src.xiaoe.client.requests.Session.get')
def test_get_access_token_http_error(mock_get, client):
    """Test handling HTTP error (e.g., 4xx/5xx) during token fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_get.return_value = mock_response

    with pytest.raises(XiaoeError) as excinfo:
        client._get_access_token()
    
    assert excinfo.value.code == -2 
    assert "Network error" in str(excinfo.value) 
    assert isinstance(excinfo.value.__cause__, requests.exceptions.HTTPError) # Should pass after fix


# --- Test _make_request ---

@patch.object(XiaoeClient, '_get_access_token', return_value="mock_valid_token")
@patch('src.xiaoe.client.requests.Session.request') 
def test_make_request_success(mock_session_request, mock_get_token, client):
    """Test _make_request handles a successful API call (code=0)."""
    api_path = "test.endpoint/v1"
    request_payload = {"filter": "value"}
    mock_api_response = {
        "code": 0,
        "msg": "Success",
        "data": {"result_key": "result_value"}
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response
    mock_response.raise_for_status.return_value = None
    mock_session_request.return_value = mock_response

    result = client._make_request("POST", api_path, data=request_payload)

    assert result == mock_api_response["data"]
    mock_get_token.assert_called_once()
    
    expected_url = f"{client.base_url}{api_path}"
    expected_json_body = request_payload.copy()
    expected_json_body['access_token'] = "mock_valid_token"
    
    mock_session_request.assert_called_once_with(
        method="POST",
        url=expected_url,
        params=None,
        json=expected_json_body,
        headers=client._session.headers,
        timeout=30
    )

@patch.object(XiaoeClient, '_get_access_token', return_value="mock_valid_token")
@patch('src.xiaoe.client.requests.Session.request')
def test_make_request_success_no_data_field(mock_session_request, mock_get_token, client):
    """Test _make_request handles success (code=0) but no 'data' field in response."""
    api_path = "action.perform/v1"
    mock_api_response = {"code": 0, "msg": "Action completed"}
    
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response
    mock_response.raise_for_status.return_value = None
    mock_session_request.return_value = mock_response

    result = client._make_request("POST", api_path)

    assert result == mock_api_response 
    mock_get_token.assert_called_once()
    mock_session_request.assert_called_once()
    call_kwargs = mock_session_request.call_args.kwargs
    assert call_kwargs['json'] == {'access_token': "mock_valid_token"}

@patch.object(XiaoeClient, '_get_access_token', return_value="mock_valid_token")
@patch('src.xiaoe.client.requests.Session.request')
def test_make_request_api_error_code_not_zero(mock_session_request, mock_get_token, client):
    """Test _make_request handles API error (code != 0)."""
    api_path = "resource.get/v1"
    error_code = 40001
    error_msg = "Invalid parameter"
    mock_api_response = {"code": error_code, "message": error_msg, "details": "id missing"}
    
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response
    mock_response.raise_for_status.return_value = None
    mock_session_request.return_value = mock_response

    with pytest.raises(XiaoeError) as excinfo:
        client._make_request("GET", api_path, params={"invalid": True})
    
    assert excinfo.value.code == error_code
    assert error_msg in str(excinfo.value)
    assert excinfo.value.details == mock_api_response
    mock_get_token.assert_called_once()
    mock_session_request.assert_called_once()

@patch.object(XiaoeClient, '_get_access_token', return_value="mock_valid_token")
@patch('src.xiaoe.client.requests.Session.request')
def test_make_request_http_error(mock_session_request, mock_get_token, client):
    """Test _make_request handles HTTP errors (e.g., 404, 500)."""
    api_path = "resource.delete/v1"
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "The requested resource does not exist."
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("msg", "doc", 0)
    mock_session_request.return_value = mock_response

    with pytest.raises(XiaoeError) as excinfo:
        client._make_request("DELETE", api_path, data={"id": "123"})

    assert excinfo.value.code == 404
    assert mock_response.text in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, requests.exceptions.HTTPError)
    mock_get_token.assert_called_once()
    mock_session_request.assert_called_once()

@patch.object(XiaoeClient, '_get_access_token', return_value="mock_valid_token")
@patch('src.xiaoe.client.requests.Session.request')
def test_make_request_http_error_with_json_body(mock_session_request, mock_get_token, client):
    """Test _make_request handles HTTP errors that return a JSON body."""
    api_path = "resource.update/v1"
    error_code = 50001
    error_msg = "Internal processing error"
    mock_api_error_body = {"code": error_code, "message": error_msg, "trace_id": "xyz"}
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.json.return_value = mock_api_error_body
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_session_request.return_value = mock_response

    with pytest.raises(XiaoeError) as excinfo:
        client._make_request("PUT", api_path, data={"id": "456", "value": "new"})

    assert excinfo.value.code == error_code 
    assert error_msg in str(excinfo.value)
    assert excinfo.value.details == mock_api_error_body
    assert isinstance(excinfo.value.__cause__, requests.exceptions.HTTPError)
    mock_get_token.assert_called_once()
    mock_session_request.assert_called_once()


@patch.object(XiaoeClient, '_get_access_token', return_value="mock_valid_token")
@patch('src.xiaoe.client.requests.Session.request')
def test_make_request_network_error(mock_session_request, mock_get_token, client):
    """Test _make_request handles network errors."""
    api_path = "another.endpoint/v1"
    error_msg = "Failed to establish a new connection"
    mock_session_request.side_effect = requests.exceptions.ConnectionError(error_msg)

    with pytest.raises(XiaoeError) as excinfo:
        client._make_request("POST", api_path)
    
    assert excinfo.value.code == -2
    assert "Network error" in str(excinfo.value)
    assert error_msg in str(excinfo.value)
    mock_get_token.assert_called_once()
    mock_session_request.assert_called_once()

# --- Test Specific API Methods ---

@patch.object(XiaoeClient, '_make_request')
def test_get_users_list_basic(mock_make_request, client):
    """Test get_users_list calls _make_request with correct basic parameters."""
    mock_response_data = {"list": [{"user_id": "u_123"}], "total": 1}
    mock_make_request.return_value = mock_response_data

    page_size = 30
    result = client.get_users_list(page_size=page_size)

    assert result == mock_response_data
    expected_payload = {"page_size": page_size}
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.user.batch.get/2.0.0",
        data=expected_payload
    )

@patch.object(XiaoeClient, '_make_request')
def test_get_users_list_with_es_skip_and_filters(mock_make_request, client):
    """Test get_users_list with es_skip and additional kwargs filters."""
    mock_response_data = {"list": [{"user_id": "u_456"}], "total": 5}
    mock_make_request.return_value = mock_response_data

    page_size = 50
    es_skip_data = {"user_id": "u_prev", "sort_value": 12345}
    filters = {"nickname": "test", "user_created_start": "2023-01-01 00:00:00", "invalid_filter": None, "empty_filter": ""}
    
    result = client.get_users_list(page_size=page_size, es_skip=es_skip_data, **filters)

    assert result == mock_response_data
    expected_payload = {
        "page_size": page_size,
        "es_skip": es_skip_data,
        "nickname": "test",
        "user_created_start": "2023-01-01 00:00:00"
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.user.batch.get/2.0.0",
        data=expected_payload
    )

def test_get_users_list_invalid_page_size(client):
    """Test get_users_list raises ValueError for invalid page_size."""
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_users_list(page_size=0)
    
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_users_list(page_size=51)


# --- Tests for get_order_list ---

@patch.object(XiaoeClient, '_make_request')
def test_get_order_list_basic(mock_make_request, client):
    """Test get_order_list calls _make_request with correct basic parameters."""
    mock_response_data = {"list": [{"order_id": "o_1"}], "total": 1, "page": 1, "page_size": 10}
    mock_make_request.return_value = mock_response_data

    search_type = 1
    start_time = "2024-01-01 00:00:00"
    end_time = "2024-01-31 23:59:59"
    page = 1
    page_size = 10

    result = client.get_order_list(
        search_type=search_type, 
        start_time=start_time, 
        end_time=end_time, 
        page=page, 
        page_size=page_size
    )

    assert result == mock_response_data
    expected_payload = {
        "search_type": search_type,
        "start_time": start_time,
        "end_time": end_time,
        "page": page,
        "page_size": page_size
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.ecommerce.order.list/1.0.0",
        data=expected_payload
    )

@patch.object(XiaoeClient, '_make_request')
def test_get_order_list_with_filters(mock_make_request, client):
    """Test get_order_list with additional kwargs filters."""
    mock_response_data = {"list": [], "total": 0, "page": 2, "page_size": 50}
    mock_make_request.return_value = mock_response_data

    search_type = 2
    start_time = "2024-02-01 00:00:00"
    end_time = "2024-02-29 23:59:59"
    page = 2
    page_size = 50
    filters = {"order_state": 1, "user_id": "u_789", "empty_filter": ""}

    result = client.get_order_list(
        search_type=search_type, 
        start_time=start_time, 
        end_time=end_time, 
        page=page, 
        page_size=page_size,
        **filters
    )

    assert result == mock_response_data
    expected_payload = {
        "search_type": search_type,
        "start_time": start_time,
        "end_time": end_time,
        "page": page,
        "page_size": page_size,
        "order_state": 1,
        "user_id": "u_789"
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.ecommerce.order.list/1.0.0",
        data=expected_payload
    )

def test_get_order_list_invalid_page_size(client):
    """Test get_order_list raises ValueError for invalid page_size."""
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_order_list(search_type=1, start_time="t", end_time="t", page_size=0)
    
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_order_list(search_type=1, start_time="t", end_time="t", page_size=51)


# --- Tests for get_order_details ---

@patch.object(XiaoeClient, '_make_request')
def test_get_order_details(mock_make_request, client):
    """Test get_order_details calls _make_request with correct parameters."""
    mock_response_data = {"order_id": "o_123", "buyer_info": {"nickname": "test"}}
    mock_make_request.return_value = mock_response_data
    
    order_id = "o_12345xyz"
    result = client.get_order_details(order_id=order_id)

    assert result == mock_response_data
    expected_payload = {"order_id": order_id}
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.ecommerce.order.detail/1.0.0",
        data=expected_payload
    )


# --- Tests for get_aftersale_list ---

@patch.object(XiaoeClient, '_make_request')
def test_get_aftersale_list_basic(mock_make_request, client):
    """Test get_aftersale_list calls _make_request with nested pagination."""
    mock_response_data = {"list": [{"aftersale_id": "a_1"}], "row_count": 1}
    mock_make_request.return_value = mock_response_data

    page_index = 1
    page_size = 20

    result = client.get_aftersale_list(page_index=page_index, page_size=page_size)

    assert result == mock_response_data
    expected_payload = {
        "data": {
            "page_index": page_index,
            "page_size": page_size
        }
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.aftersale.list/1.0.0",
        data=expected_payload
    )

@patch.object(XiaoeClient, '_make_request')
def test_get_aftersale_list_with_filters(mock_make_request, client):
    """Test get_aftersale_list with additional kwargs filters nested under data."""
    mock_response_data = {"list": [], "row_count": 0}
    mock_make_request.return_value = mock_response_data

    page_index = 3
    page_size = 50
    filters = {"state": 4, "created_at_start": "2024-01-01 00:00:00", "empty": ""}

    result = client.get_aftersale_list(page_index=page_index, page_size=page_size, **filters)

    assert result == mock_response_data
    expected_payload = {
        "data": {
            "page_index": page_index,
            "page_size": page_size,
            "state": 4,
            "created_at_start": "2024-01-01 00:00:00"
        }
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.aftersale.list/1.0.0",
        data=expected_payload
    )

def test_get_aftersale_list_invalid_page_size(client):
    """Test get_aftersale_list raises ValueError for invalid page_size."""
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_aftersale_list(page_size=0)
    
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_aftersale_list(page_size=51)


# --- Tests for get_aftersale_details ---

@patch.object(XiaoeClient, '_make_request')
def test_get_aftersale_details_basic(mock_make_request, client):
    """Test get_aftersale_details calls _make_request with required id."""
    mock_response_data = {"aftersale_id": "a_123", "reason": "test reason"}
    mock_make_request.return_value = mock_response_data
    
    aftersale_id = "a_12345xyz"
    result = client.get_aftersale_details(aftersale_id=aftersale_id)

    assert result == mock_response_data
    expected_payload = {"aftersale_id": aftersale_id}
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.aftersale.detail/1.0.0",
        data=expected_payload
    )

@patch.object(XiaoeClient, '_make_request')
def test_get_aftersale_details_with_optional_ids(mock_make_request, client):
    """Test get_aftersale_details with optional user_id and order_id."""
    mock_response_data = {"aftersale_id": "a_456"}
    mock_make_request.return_value = mock_response_data
    
    aftersale_id = "a_456abc"
    user_id = "u_test"
    order_id = "o_test"
    result = client.get_aftersale_details(
        aftersale_id=aftersale_id, 
        user_id=user_id, 
        order_id=order_id
    )

    assert result == mock_response_data
    expected_payload = {
        "aftersale_id": aftersale_id,
        "user_id": user_id,
        "order_id": order_id
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.aftersale.detail/1.0.0",
        data=expected_payload
    )


# --- Tests for get_user_info_batch ---

@patch.object(XiaoeClient, '_make_request')
def test_get_user_info_batch(mock_make_request, client):
    """Test get_user_info_batch calls _make_request with correct parameters."""
    mock_response_data = {"users": [{"user_id": "u_1"}, {"user_id": "u_2"}]}
    mock_make_request.return_value = mock_response_data
    
    user_ids = ["u_abc", "u_def"]
    result = client.get_user_info_batch(user_ids=user_ids)

    assert result == mock_response_data
    expected_payload = {"user_ids": user_ids}
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.user.info.batch.get/1.0.0",
        data=expected_payload
    )

def test_get_user_info_batch_empty_list(client):
    """Test get_user_info_batch raises ValueError for empty user_ids list."""
    with pytest.raises(ValueError, match="user_ids list cannot be empty"):
        client.get_user_info_batch(user_ids=[])

@patch('src.xiaoe.client.logger.warning')
@patch.object(XiaoeClient, '_make_request')
def test_get_user_info_batch_too_many_ids_logs_warning(mock_make_request, mock_logger_warning, client):
    """Test get_user_info_batch logs a warning if more than 100 user_ids are provided."""
    mock_make_request.return_value = {"users": []}
    
    user_ids_long = [f"u_{i}" for i in range(101)]
    client.get_user_info_batch(user_ids=user_ids_long)

    mock_logger_warning.assert_called_once()
    args, _ = mock_logger_warning.call_args
    assert "contains > 100 user_ids" in args[0]
    
    expected_payload = {"user_ids": user_ids_long}
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.user.info.batch.get/1.0.0",
        data=expected_payload
    )


# --- Tests for get_goods_relations ---

@patch.object(XiaoeClient, '_make_request')
def test_get_goods_relations_basic(mock_make_request, client):
    """Test get_goods_relations calls _make_request with default pagination."""
    mock_response_data = {"list": [{"id": "g_1"}], "total": 1, "current_page": 1}
    mock_make_request.return_value = mock_response_data

    result = client.get_goods_relations()

    assert result == mock_response_data
    expected_payload = {
        "page_index": 1,
        "page_size": 10
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.goods.relations.get/2.0.0",
        data=expected_payload
    )

@patch.object(XiaoeClient, '_make_request')
def test_get_goods_relations_with_params_and_filters(mock_make_request, client):
    """Test get_goods_relations with specific pagination and filters."""
    mock_response_data = {"list": [], "total": 0, "current_page": 5}
    mock_make_request.return_value = mock_response_data

    page_index = 5
    page_size = 30
    filters = {"goods_type": 6, "sale_status": 1, "keyword": "test", "ids": ["g_1", "g_2"], "empty": ""}

    result = client.get_goods_relations(page_index=page_index, page_size=page_size, **filters)

    assert result == mock_response_data
    expected_payload = {
        "page_index": page_index,
        "page_size": page_size,
        "goods_type": 6,
        "sale_status": 1,
        "keyword": "test",
        "ids": ["g_1", "g_2"]
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.goods.relations.get/2.0.0",
        data=expected_payload
    )

@patch('src.xiaoe.client.logger.warning')
@patch.object(XiaoeClient, '_make_request')
def test_get_goods_relations_too_many_ids_logs_warning(mock_make_request, mock_logger_warning, client):
    """Test get_goods_relations logs warning if more than 20 ids are provided."""
    mock_make_request.return_value = {"list": [], "total": 0}
    
    long_ids_list = [f"g_{i}" for i in range(21)]
    client.get_goods_relations(ids=long_ids_list)

    mock_logger_warning.assert_called_once()
    args, _ = mock_logger_warning.call_args
    assert "exceeds the limit of 20" in args[0]

    expected_payload = {
        "page_index": 1,
        "page_size": 10,
        "ids": long_ids_list 
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.goods.relations.get/2.0.0",
        data=expected_payload
    )

def test_get_goods_relations_invalid_page_size(client):
    """Test get_goods_relations raises ValueError for invalid page_size."""
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_goods_relations(page_size=0)
    
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_goods_relations(page_size=51)


# --- Tests for get_user_orders ---

@patch.object(XiaoeClient, '_make_request')
def test_get_user_orders_basic(mock_make_request, client):
    """Test get_user_orders calls _make_request with required user_id and default pagination."""
    mock_response_data = {"list": [{"order_id": "o_u1_1"}], "total": 1}
    mock_make_request.return_value = mock_response_data

    user_id = "u_test_123"

    result = client.get_user_orders(user_id=user_id)

    assert result == mock_response_data
    expected_payload = {
        "user_id": user_id,
        "data": {
            "page_index": 1,
            "page_size": 10
        }
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.get.user.orders/1.0.0",
        data=expected_payload
    )

@patch.object(XiaoeClient, '_make_request')
def test_get_user_orders_with_params_and_filters(mock_make_request, client):
    """Test get_user_orders with specific pagination and filters nested under data."""
    mock_response_data = {"list": [], "total": 0}
    mock_make_request.return_value = mock_response_data

    user_id = "u_test_456"
    page_index = 4
    page_size = 40
    filters = {"order_state": 1, "resource_type": 6, "order_by": "pay_time:asc", "empty": ""}

    result = client.get_user_orders(
        user_id=user_id, 
        page_index=page_index, 
        page_size=page_size, 
        **filters
    )

    assert result == mock_response_data
    expected_payload = {
        "user_id": user_id,
        "data": {
            "page_index": page_index,
            "page_size": page_size,
            "order_state": 1,
            "resource_type": 6,
            "order_by": "pay_time:asc"
        }
    }
    mock_make_request.assert_called_once_with(
        "POST",
        "xe.get.user.orders/1.0.0",
        data=expected_payload
    )

def test_get_user_orders_invalid_page_size(client):
    """Test get_user_orders raises ValueError for invalid page_size."""
    user_id = "u_test_789"
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_user_orders(user_id=user_id, page_size=0)
    
    with pytest.raises(ValueError, match="page_size must be between 1 and 50"):
        client.get_user_orders(user_id=user_id, page_size=51)

# All client methods based on provided docs should now have basic tests.
import pytest
import os
from src.xiaoe.client import XiaoeClient, XiaoeError
from src.core.config import settings

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

# Helper to check if required settings are available for integration tests
def credentials_available():
    return all([
        settings.XIAOE_APP_ID,
        settings.XIAOE_CLIENT_ID,
        settings.XIAOE_SECRET_KEY
    ])

# Conditionally skip tests if credentials are not found
requires_credentials = pytest.mark.skipif(
    not credentials_available(),
    reason="Skipping integration test: Xiaoe credentials not found in settings (check .env file)."
)

@requires_credentials
def test_integration_get_access_token_success():
    """
    Tests if the client can successfully obtain an access token 
    using credentials from the environment/settings.
    """
    print(f"\nAttempting integration test with App ID: {settings.XIAOE_APP_ID[:5]}..." ) # Avoid logging full ID
    try:
        # Initialize client - it will load settings automatically
        client = XiaoeClient() 
        
        # Call the internal method to fetch the token (or get cached)
        # In a real scenario, we might test a public method that triggers this,
        # but for direct token testing, calling the internal method is fine.
        token = client._get_access_token() 

        print(f"Successfully obtained token (first 5 chars): {token[:5]}...")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 10 # Basic sanity check for token format/length
        assert client._access_token == token
        assert client._token_expires_at > 0

    except XiaoeError as e:
        pytest.fail(f"XiaoeError occurred during token fetch: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")

@requires_credentials
def test_integration_get_users_list_small():
    """
    Tests fetching a small number of users using the get_users_list method.
    Verifies successful API call and basic response structure.
    """
    print(f"\nAttempting to fetch 1 user with App ID: {settings.XIAOE_APP_ID[:5]}...")
    try:
        client = XiaoeClient()
        page_size_to_test = 1
        
        # Use the public method
        response_data = client.get_users_list(page_size=page_size_to_test)

        print(f"Successfully called get_users_list. Response keys: {response_data.keys()}")

        # Basic validation of the response structure
        assert isinstance(response_data, dict)
        assert 'list' in response_data
        assert 'total' in response_data
        assert isinstance(response_data['list'], list)
        
        # Check if the number of returned users matches expectations (can be 0 up to page_size)
        assert len(response_data['list']) <= page_size_to_test 
        if response_data['total'] > 0:
             assert len(response_data['list']) > 0 # If total > 0, list shouldn't be empty unless page_size=0 (which we didn't request)
        else:
             assert len(response_data['list']) == 0 # If total is 0, list must be empty

        print(f"Found {len(response_data['list'])} user(s), total reported: {response_data['total']}.")

    except XiaoeError as e:
        pytest.fail(f"XiaoeError occurred during get_users_list call: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during get_users_list: {e}")

# Add more integration tests below... 
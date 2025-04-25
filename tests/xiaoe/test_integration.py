import pytest
import os

# Ensure config is loaded before importing client if run directly
from src.core.config import settings 
from src.xiaoe.client import XiaoeClient, XiaoeError

# Skip integration tests if credentials are not set
pytestmark = pytest.mark.skipif(
    not all([
        settings.XIAOE_APP_ID,
        settings.XIAOE_CLIENT_ID,
        settings.XIAOE_SECRET_KEY
    ]),
    reason="Xiaoe credentials not found in environment for integration tests."
)

# Mark tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture(scope="module")
def live_client() -> XiaoeClient:
    """Provides a XiaoeClient instance configured with real credentials."""
    # Client will automatically pick up credentials from settings -> env
    return XiaoeClient()

@pytest.mark.integration # Explicitly mark as integration test
def test_live_get_access_token(live_client):
    """Test fetching a real access token from the live API."""
    print("\nAttempting to fetch live access token...")
    try:
        token = live_client._get_access_token()
        print(f"Successfully fetched token (first few chars): {token[:5]}...")
        assert isinstance(token, str)
        assert len(token) > 10 # Check if token seems valid
    except XiaoeError as e:
        pytest.fail(f"Failed to get live access token: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during live token fetch: {e}")

@pytest.mark.integration
def test_live_get_users_list(live_client):
    """Test fetching the first page of users from the live API using v2.0.0 endpoint."""
    print("\nAttempting to fetch live user list (v2.0.0 - first page, size 1)...")
    try:
        # Fetch only 1 user from the first page (no es_skip)
        response_data = live_client.get_users_list(page_size=1) 
        print(f"Successfully fetched user list response.")
        
        # Validate response structure based on v2.0.0 documentation
        assert isinstance(response_data, dict)
        assert "list" in response_data
        assert isinstance(response_data['list'], list)
        assert "total" in response_data # v2 uses 'total'
        assert isinstance(response_data['total'], int)
        print(f"Total users found: {response_data['total']}")
        
        # Check list content if not empty
        if response_data['list']:
            assert len(response_data['list']) == 1 # Because we requested page_size=1
            first_user = response_data['list'][0]
            print(f"First user data keys: {list(first_user.keys())}")
            assert "user_id" in first_user
            assert "es_skip" in first_user # Check if pagination cursor is present
            assert isinstance(first_user["es_skip"], dict)
            assert "id" in first_user["es_skip"]
            assert "user_created_at" in first_user["es_skip"]
        else:
            print("User list is empty.")

    except XiaoeError as e:
        pytest.fail(f"Failed to get live user list: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during live user list fetch: {e}") 
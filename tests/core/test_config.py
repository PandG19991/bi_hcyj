import os
import pytest
from unittest.mock import patch

# Important: Import modules *after* potentially patching environment variables
# This ensures the module reads the patched values during import time.

@pytest.fixture(autouse=True)
def clear_env_vars():
    """Fixture to clear relevant env vars before each test."""
    vars_to_clear = [
        "XIAOE_APP_ID", "XIAOE_CLIENT_ID", "XIAOE_SECRET_KEY",
        "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME",
        "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_DB_NAME",
        "LOG_LEVEL"
    ]
    original_values = {var: os.environ.get(var) for var in vars_to_clear}
    for var in vars_to_clear:
        if var in os.environ:
            del os.environ[var]
    yield
    # Restore original values after test
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]

def test_settings_load_from_env(mocker):
    """Test that settings are loaded correctly from environment variables."""
    test_values = {
        "XIAOE_APP_ID": "test_app_id",
        "XIAOE_CLIENT_ID": "test_client_id",
        "XIAOE_SECRET_KEY": "test_secret",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pw",
        "DB_HOST": "testhost",
        "DB_PORT": "1234",
        "DB_NAME": "testdb",
        "MYSQL_USER": "mysql_user",
        "MYSQL_PASSWORD": "mysql_pw",
        "MYSQL_HOST": "mysqlhost",
        "MYSQL_PORT": "4321",
        "MYSQL_DB_NAME": "mysqldb",
        "LOG_LEVEL": "DEBUG"
    }
    mocker.patch.dict(os.environ, test_values)
    mocker.patch('src.core.config.load_dotenv', return_value=False) # Prevent .env override

    # Import config *after* patching environment
    from src.core import config

    assert config.settings.XIAOE_APP_ID == "test_app_id"
    assert config.settings.XIAOE_CLIENT_ID == "test_client_id"
    assert config.settings.XIAOE_SECRET_KEY == "test_secret"
    assert config.settings.DB_USER == "test_user"
    assert config.settings.DB_PASSWORD == "test_pw"
    assert config.settings.DB_HOST == "testhost"
    assert config.settings.DB_PORT == "1234"
    assert config.settings.DB_NAME == "testdb"
    assert config.settings.MYSQL_USER == "mysql_user"
    assert config.settings.MYSQL_PASSWORD == "mysql_pw"
    assert config.settings.MYSQL_HOST == "mysqlhost"
    assert config.settings.MYSQL_PORT == "4321"
    assert config.settings.MYSQL_DB_NAME == "mysqldb"
    assert config.settings.LOG_LEVEL == "DEBUG"

def test_settings_defaults(mocker):
    """Test that settings use default values when env vars are not set."""
    # Env vars cleared by fixture
    # Ensure .env is not loaded for this test
    mocker.patch('src.core.config.load_dotenv', return_value=False)

    # Import config *after* patching load_dotenv
    from src.core import config

    assert config.settings.XIAOE_APP_ID is None
    assert config.settings.XIAOE_CLIENT_ID is None
    assert config.settings.XIAOE_SECRET_KEY is None
    assert config.settings.DB_USER is None
    assert config.settings.DB_PASSWORD is None
    assert config.settings.DB_HOST == "localhost" # Default
    assert config.settings.DB_PORT == "5432"      # Default
    assert config.settings.DB_NAME is None
    assert config.settings.MYSQL_USER is None
    assert config.settings.MYSQL_PASSWORD is None
    assert config.settings.MYSQL_HOST == "localhost" # Default
    assert config.settings.MYSQL_PORT == "3306"      # Default
    assert config.settings.MYSQL_DB_NAME is None
    assert config.settings.LOG_LEVEL == "INFO"     # Default

def test_get_pgsql_database_url_success(mocker):
    """Test the PostgreSQL database URL construction with all values set."""
    mocker.patch.dict(os.environ, {
        "DB_USER": "pguser",
        "DB_PASSWORD": "pgpass",
        "DB_HOST": "pghost",
        "DB_PORT": "5433",
        "DB_NAME": "pgdb"
    })
    mocker.patch('src.core.config.load_dotenv', return_value=False) # Prevent .env override

    # Import config *after* patching environment
    from src.core import config
    expected_url = "postgresql://pguser:pgpass@pghost:5433/pgdb"
    assert config.get_pgsql_database_url() == expected_url

def test_get_pgsql_database_url_fail_missing_values(mocker):
    """Test the PostgreSQL database URL construction fails with missing values."""
    # Env vars are cleared by the autouse fixture
    mocker.patch.dict(os.environ, {"DB_USER": "pguser_only"}) # Set only one value
    mocker.patch('src.core.config.load_dotenv', return_value=False) # Prevent .env load

    # Import config *after* patching
    from src.core import config
    assert config.get_pgsql_database_url() is None

def test_get_mysql_database_url_success(mocker):
    """Test the MySQL database URL construction with all values set."""
    mocker.patch.dict(os.environ, {
        "MYSQL_USER": "mysqluser",
        "MYSQL_PASSWORD": "mysqlpass",
        "MYSQL_HOST": "mysqlhost",
        "MYSQL_PORT": "3307",
        "MYSQL_DB_NAME": "mysqldb"
    })
    mocker.patch('src.core.config.load_dotenv', return_value=False) # Prevent .env override

    # Import config *after* patching environment
    from src.core import config
    expected_url = "mysql+mysqlconnector://mysqluser:mysqlpass@mysqlhost:3307/mysqldb"
    assert config.get_mysql_database_url() == expected_url

def test_get_mysql_database_url_fail_missing_values(mocker):
    """Test the MySQL database URL construction fails with missing values."""
    # Env vars are cleared by the autouse fixture
    mocker.patch.dict(os.environ, {"MYSQL_USER": "mysqluser_only"}) # Set only one value
    mocker.patch('src.core.config.load_dotenv', return_value=False) # Prevent .env load

    # Import config *after* patching
    from src.core import config
    assert config.get_mysql_database_url() is None

# Example of testing .env file loading (Optional, requires creating a test .env)
# def test_settings_load_from_dotenv_file(tmp_path, mocker):
#     dotenv_content = """
# XIAOE_APP_ID=dotenv_app_id
# LOG_LEVEL=WARNING
# """
#     dotenv_file = tmp_path / ".env"
#     dotenv_file.write_text(dotenv_content)
#
#     # Mock load_dotenv to use the temp file's directory
#     mocker.patch('src.core.config.load_dotenv') # Prevent default load
#     # Need to specifically call load_dotenv with the path in the test
#     from dotenv import load_dotenv
#     load_dotenv(dotenv_path=dotenv_file)
#
#     # Import config *after* loading the test .env
#     from src.core import config
#
#     assert config.settings.XIAOE_APP_ID == "dotenv_app_id"
#     assert config.settings.LOG_LEVEL == "WARNING"
#     assert config.settings.XIAOE_CLIENT_ID is None # Not in file
#
# # def test_settings_load_from_dotenv_file(tmp_path, mocker):
#     dotenv_content = """
# XIAOE_APP_ID=dotenv_app_id
# LOG_LEVEL=WARNING
# """
#     dotenv_file = tmp_path / ".env"
#     dotenv_file.write_text(dotenv_content)
#
#     # Mock load_dotenv to use the temp file's directory
#     mocker.patch('src.core.config.load_dotenv') # Prevent default load
#     # Need to specifically call load_dotenv with the path in the test
#     from dotenv import load_dotenv
#     load_dotenv(dotenv_path=dotenv_file)
#
#     # Import config *after* loading the test .env
#     from src.core import config
#
#     assert config.settings.XIAOE_APP_ID == "dotenv_app_id"
#     assert config.settings.LOG_LEVEL == "WARNING"
#     assert config.settings.XIAOE_CLIENT_ID is None # Not in file 
import logging
import pytest
import io
import os
from unittest.mock import patch, MagicMock

# Similar to test_config, need to handle module import timing with mocks

# Placeholder for logging configuration tests
import pytest
import logging

# Assuming your logger setup is in src.core.logger
# Import both logger object and the setup function
from src.core.logger import logger as global_logger, setup_logger, PROJECT_NAME 

# Need to import sys for the logger module itself
import sys

# REMOVED autouse fixture as it might interfere with the dedicated test_logger
# @pytest.fixture(autouse=True)
# def setup_and_teardown_logger():
#     ...
    
@pytest.fixture
def mock_settings(mocker):
    """Fixture to provide a mock settings object."""
    mock = mocker.MagicMock()
    mock.LOG_LEVEL = "INFO" # Default log level for tests unless overridden
    return mock

# Use a separate logger instance for testing to avoid conflicts with global state
@pytest.fixture
def test_logger():
    """Provides a clean logger instance for testing setup."""
    # Use a unique name for the test logger instance
    logger_name = f"test_logger_{PROJECT_NAME}"
    _test_logger = logging.getLogger(logger_name)
    # Ensure it starts clean (handlers and level)
    _test_logger.handlers = []
    _test_logger.setLevel(logging.WARNING) # Set a default starting level
    yield _test_logger
    # Clean up handlers added during the test
    for handler in _test_logger.handlers[:]:
        _test_logger.removeHandler(handler)

def test_logger_initialization(mock_settings, mocker, test_logger):
    """Test logger is initialized with correct name and default level."""
    mocker.patch('src.core.logger.settings', mock_settings)
    # Pass the specific test_logger instance to setup_logger
    setup_logger(log_level_str=mock_settings.LOG_LEVEL, logger_instance=test_logger)

    assert test_logger.name.endswith(PROJECT_NAME) # Check name part
    assert test_logger.level == logging.INFO # Should be INFO as set by setup
    assert len(test_logger.handlers) == 1 # Should have one handler

def test_logger_level_from_settings(mock_settings, mocker, test_logger):
    """Test logger level is set correctly based on settings."""
    mock_settings.LOG_LEVEL = "DEBUG" 
    mocker.patch('src.core.logger.settings', mock_settings)
    setup_logger(log_level_str=mock_settings.LOG_LEVEL, logger_instance=test_logger)
    assert test_logger.level == logging.DEBUG

    # Reset handlers on the test_logger before setting up again
    print(f"[DEBUG test] Resetting handlers for {test_logger.name} (id: {id(test_logger)})") # DEBUG
    test_logger.handlers = [] 
    mock_settings.LOG_LEVEL = "WARNING"
    print(f"[DEBUG test] Calling setup_logger for WARNING level on {test_logger.name} (id: {id(test_logger)})") # DEBUG
    setup_logger(log_level_str=mock_settings.LOG_LEVEL, logger_instance=test_logger)
    print(f"[DEBUG test] Level after setup for WARNING: {test_logger.level}") # DEBUG
    assert test_logger.level == logging.WARNING

def test_log_message_format(mock_settings, mocker, test_logger, caplog): # Use caplog and test_logger
    """Test that log messages have the expected format and level."""
    mock_settings.LOG_LEVEL = "INFO" # Set level to INFO for this test
    mocker.patch('src.core.logger.settings', mock_settings)
    # Setup the specific test_logger instance
    setup_logger(log_level_str=mock_settings.LOG_LEVEL, logger_instance=test_logger)

    test_message_info = "This is an info test."
    test_message_warn = "This is a warning test."
    
    # Log messages using the test_logger instance
    test_logger.info(test_message_info)
    test_logger.warning(test_message_warn)
    test_logger.debug("This debug message should NOT be logged.") # Level is INFO

    # Check captured logs using caplog - it captures from all loggers by default
    # Filter records for our specific test logger if needed
    test_logger_records = [r for r in caplog.records if r.name == test_logger.name]
    
    # Filter out the configuration message added by setup_logger itself
    test_logger_records = [r for r in test_logger_records if not r.message.startswith("Logger '") or not r.message.endswith("' configured with level INFO.")]

    assert len(test_logger_records) == 2 # INFO and WARNING should be logged by test_logger
    
    # Check first record (INFO)
    assert test_logger_records[0].levelname == "INFO"
    assert test_logger_records[0].message == test_message_info
    
    # Check second record (WARNING)
    assert test_logger_records[1].levelname == "WARNING"
    assert test_logger_records[1].message == test_message_warn

def test_logger_handler_addition_idempotency(mock_settings, mocker, test_logger):
    """Test that calling setup_logger multiple times doesn't add duplicate handlers."""
    mock_settings.LOG_LEVEL = "INFO"
    mocker.patch('src.core.logger.settings', mock_settings)

    # Setup the specific test_logger instance
    setup_logger(log_level_str=mock_settings.LOG_LEVEL, logger_instance=test_logger)
    initial_handler_count = len(test_logger.handlers)
    assert initial_handler_count > 0 # Should have at least one handler after setup

    # Call setup again (should be blocked by idempotency check)
    setup_logger(log_level_str=mock_settings.LOG_LEVEL, logger_instance=test_logger)
    
    assert len(test_logger.handlers) == initial_handler_count # Count should remain the same 
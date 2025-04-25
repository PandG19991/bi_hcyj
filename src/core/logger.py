import logging
import sys
from typing import Optional

# Import settings to access LOG_LEVEL
from src.core.config import settings 

# Define project name for logger identification
PROJECT_NAME = "data_sync_project"

# Get the root logger - THIS is the instance we will configure and use globally
logger = logging.getLogger(PROJECT_NAME)

# REMOVED DEFAULT_LOGGER_NAME as we configure the global one

# --- Configuration --- 
def setup_logger(log_level_str: Optional[str] = None, 
                   log_file: Optional[str] = None):
    """Configures the global project logger instance.

    Args:
        log_level_str: Optional logging level string (e.g., 'DEBUG', 'INFO'). 
                       If None, uses LOG_LEVEL from settings (defaulting to INFO).
        log_file: Optional path to a file where logs should also be written.
    """
    # Determine log level: use provided string, fallback to settings, default to INFO
    level_str_to_use = log_level_str if log_level_str else settings.LOG_LEVEL
    log_level = getattr(logging, level_str_to_use.upper(), logging.INFO) 
    
    # Use the global logger instance directly
    # logger = logging.getLogger(logger_name) # No longer needed
    
    # Prevent adding multiple handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(log_level) 

    # Define log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # --- Console Handler --- 
    ch = logging.StreamHandler(sys.stdout) # Explicitly use stdout
    ch.setLevel(log_level) 
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # --- File Handler (Optional) ---
    if log_file:
        try:
            fh = logging.FileHandler(log_file, encoding='utf-8') # Use utf-8 encoding
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            # logger.info(f"Logging also configured to file: {log_file}") # Logged below
        except Exception as e:
            # Use the logger we are configuring to report the error
            logger.error(f"Failed to configure file logging to {log_file}: {e}", exc_info=True)

    # logger.propagate = False # Keep commented unless needed
    
    logger.info(f"Logger '{logger.name}' configured with level {level_str_to_use.upper()}. Outputting to console{f' and file \'{log_file}\'' if log_file else ''}.")
    # logger.debug(f"Setup complete for {logger.name}") # Debug message might be too verbose here

    # No need to return the logger, setup is done on the global instance
    # return logger

# REMOVED initial setup call

# REMOVED Usage Example block 
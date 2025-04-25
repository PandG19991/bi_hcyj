import os
from dotenv import load_dotenv

# Load environment variables from .env file, if it exists
# Only load .env file if not running under pytest
if os.getenv("PYTEST_RUNNING") is None:
    load_dotenv() 
    # print("[DEBUG config.py] .env loaded.") # Removed debug print
# else:
    # print("[DEBUG config.py] PYTEST_RUNNING detected, skipping .env load.") # Removed debug print

class Settings:
    """Application configuration settings loaded from environment variables."""

    # Xiaoe Platform Credentials
    XIAOE_APP_ID: str | None = os.getenv("XIAOE_APP_ID")
    XIAOE_CLIENT_ID: str | None = os.getenv("XIAOE_CLIENT_ID")
    XIAOE_SECRET_KEY: str | None = os.getenv("XIAOE_SECRET_KEY")

    # Database Credentials (MySQL)
    MYSQL_USER: str | None = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: str | None = os.getenv("MYSQL_PASSWORD")
    MYSQL_HOST: str | None = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str | None = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB_NAME: str | None = os.getenv("MYSQL_DB_NAME")

    # Add other configurations as needed
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Create a single instance of settings to be imported across the application
settings = Settings()

# Removed get_pgsql_database_url function

def get_mysql_database_url() -> str | None:
    if all([settings.MYSQL_USER, settings.MYSQL_PASSWORD, settings.MYSQL_HOST, settings.MYSQL_PORT, settings.MYSQL_DB_NAME]):
        # Note: Adjust driver as needed (e.g., mysql+mysqlconnector, mysql+pymysql)
        return f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB_NAME}"
    return None 
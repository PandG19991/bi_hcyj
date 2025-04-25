# This file is kept for backward compatibility or example purposes.
# Configurations are now loaded from environment variables via src.core.config

# You can directly import the settings object if needed:
# from src.core.config import settings

# print(f"Loaded App ID: {settings.XIAOE_APP_ID}")

# Or define variables by reading from the settings object
# APP_ID = settings.XIAOE_APP_ID
# CLIENT_ID = settings.XIAOE_CLIENT_ID
# SECRET_KEY = settings.XIAOE_SECRET_KEY

# It's generally recommended to import `settings` directly where needed
# in your application code, rather than re-defining variables here.

# Example structure (matching .env.example and src/core/config.py):
XIAOE_APP_ID="YOUR_XIAOE_APP_ID_HERE" # Loaded from environment
XIAOE_CLIENT_ID="YOUR_XIAOE_CLIENT_ID_HERE" # Loaded from environment
XIAOE_SECRET_KEY="YOUR_XIAOE_SECRET_KEY_HERE" # Loaded from environment

DB_USER="YOUR_DB_USER"
DB_PASSWORD="YOUR_DB_PASSWORD"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="your_db_name"

MYSQL_USER="YOUR_MYSQL_USER"
MYSQL_PASSWORD="YOUR_MYSQL_PASSWORD"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_DB_NAME="your_mysql_db_name"

LOG_LEVEL="INFO" 
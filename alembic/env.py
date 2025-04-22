import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

# -- Add project root to sys.path ---
# This allows env.py to import modules from the project (like core.models)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

# -- Import Base from models and settings ---
from core.models import Base
from config.config import settings # Import settings to get DATABASE_URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# -- Set the database URL from settings ---
# Override the sqlalchemy.url from alembic.ini with the one from config.py
# This ensures we use the correct URL loaded via .env
if settings.DATABASE_URL:
    config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
else:
    # Fallback or raise an error if DATABASE_URL is not set
    # For now, let it use the (likely incorrect) default in alembic.ini or raise later
    pass

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# -- Point target_metadata to your Base ---
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include object representation for comments with autogenerate
        include_object=lambda obj, name, type_, reflected, compare_to: not (type_ == 'table' and name == 'sync_status'), # Example: exclude sync_status if needed
        process_revision_directives=process_revision_directives, # Add this if using the hook below
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use create_engine directly with the URL from settings
    # This bypasses potential issues with engine_from_config parsing
    try:
        print(f"DEBUG: Attempting to create engine with URL: {settings.DATABASE_URL}")
        engine = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    except Exception as e:
        print(f"Error creating engine: {e}") # Add print for debugging
        print(f"Using DATABASE_URL: {settings.DATABASE_URL}")
        raise

    # Optional: Add a print here to see the URL being used
    # print(f"DEBUG: Connecting with engine for URL: {settings.DATABASE_URL}")

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 比较列类型
            compare_server_default=True, # 比较服务器默认值
            # 添加 MySQL 特定的字符集和排序规则选项
            dialect_opts={"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
        )

        with context.begin_transaction():
            context.run_migrations()

# Optional: Hook to process revision directives (e.g., render comments)
# Requires imports: from alembic.script import ScriptDirectory
# from alembic.operations import Operations, MigrateOperation
# from sqlalchemy import text
def process_revision_directives(context, revision, directives):
    migration_script = directives[0]
    # Add logic here if needed, e.g., to ensure comments are rendered
    # head_revision = ScriptDirectory.from_config(context.config).get_current_head()
    # if head_revision is None:
        # Initial migration, maybe add table comments?
        # pass


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

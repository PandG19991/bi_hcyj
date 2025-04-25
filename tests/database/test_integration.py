import pytest
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
import datetime
from datetime import timezone # Import timezone

# Import necessary components from your application
# Ensure engine and SessionLocal are initialized before tests run
# If manager.py raises error on import due to no DB config, tests will fail here.
from src.database.manager import engine, get_db_session, SessionLocal
from src.database.models import Base, XiaoeUser
from src.core.config import settings # To check if DB is configured

# Skip all tests in this module if database is not configured
pytestmark = pytest.mark.skipif(
    not SessionLocal,
    reason="Database is not configured, skipping integration tests."
)

@pytest.fixture(scope="module", autouse=True)
def check_db_connection():
    """Module-level fixture to check initial DB connection."""
    if not engine:
        pytest.fail("Database engine not created. Check configuration and logs.")
    try:
        # Try connecting to the database
        with engine.connect() as connection:
            # Optionally run a simple query
            # connection.execute(text("SELECT 1"))
            pass
    except OperationalError as e:
        pytest.fail(f"Database connection failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during DB connection check: {e}")

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for each test function."""
    if not SessionLocal:
        pytest.skip("Database not configured.")

    # Normally, you'd use a testing-specific session/engine pointing to a test DB
    # For now, we use the configured DB but manage transactions carefully
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session # provide the session to the test

    # Teardown: rollback any changes made during the test
    session.close()
    transaction.rollback()
    connection.close()

def test_connection_via_session(db_session):
    """Test if we can successfully get a session and run a simple query."""
    try:
        # Example: Check alembic version table exists (created by `alembic upgrade`)
        result = db_session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        assert result.scalar_one_or_none() is not None # Check if we got a result
    except ProgrammingError as e:
        # Handle case where alembic_version might not exist if migrations failed silently
        pytest.fail(f"Query failed, possibly alembic_version table missing? Error: {e}")
    except Exception as e:
        pytest.fail(f"Failed to execute simple query via session: {e}")

def test_xiaoe_users_table_exists():
    """Test if the 'xiaoe_users' table was created by migrations."""
    inspector = inspect(engine)
    assert inspector.has_table("xiaoe_users")

def test_xiaoe_user_create_and_read(db_session):
    """Test creating a XiaoeUser record and reading it back."""
    unique_user_id = f"test_user_{datetime.datetime.now().isoformat()}"
    test_user = XiaoeUser(
        user_id=unique_user_id,
        app_id="test_app",
        nickname="Test User",
        # Use timezone-aware datetime for UTC
        created_at_platform=datetime.datetime.now(timezone.utc)
    )
    db_session.add(test_user)
    # Need to commit here within the test's transaction context
    # The fixture will roll back the overall transaction later
    db_session.commit()

    # Query the user back
    queried_user = db_session.query(XiaoeUser).filter(XiaoeUser.user_id == unique_user_id).first()

    assert queried_user is not None
    assert queried_user.user_id == unique_user_id
    assert queried_user.nickname == "Test User"
    assert queried_user.app_id == "test_app"
    assert queried_user.id is not None
    assert queried_user.created_at is not None
    assert queried_user.updated_at is not None 
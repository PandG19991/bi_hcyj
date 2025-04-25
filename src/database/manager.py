from sqlalchemy import create_engine, insert, delete, update
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.mysql import insert as mysql_insert # Import specific MySQL insert
from contextlib import contextmanager
from typing import List, Dict, Any, Generator, Type, Optional
import datetime # Added datetime

from src.core.config import settings, get_mysql_database_url
from src.core.logger import logger
from src.database.models import Base, XiaoeUser, XiaoeGoods, XiaoeOrder, XiaoeOrderItem, XiaoeAftersale, XiaoeAftersaleItem, SyncState # Import Base and specific models as needed

# --- Database Setup ---

# Get the database URL using the helper function
DATABASE_URL = get_mysql_database_url()

if not DATABASE_URL:
    logger.error("Could not construct DATABASE_URL from settings. Please check MYSQL_* variables in your .env file.")
    raise ValueError("DATABASE_URL could not be constructed.")

# Set pool_recycle to avoid MySQL connection timeouts (e.g., 3600 seconds = 1 hour)
# Set echo=False for production, True for debugging SQL statements
engine = create_engine(DATABASE_URL, pool_recycle=3600, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

def create_all_tables():
    """Create all tables defined in models.py. 
    Should be called once during application setup or handled by migrations.
    """
    logger.info("Attempting to create database tables if they don't exist...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        raise

# --- Upsert Functions ---

def _batch_upsert(db: Session, model: Type[Base], data: List[Dict[str, Any]]):
    """Generic batch upsert function using SQLAlchemy's merge.
    
    Args:
        db: The SQLAlchemy session.
        model: The SQLAlchemy model class.
        data: A list of dictionaries representing the data to upsert.
    """
    if not data:
        return 0
        
    count = 0
    try:
        for record_dict in data:
            # Create an instance of the model from the dictionary
            # Filter out keys that are not part of the model to avoid errors
            model_columns = {c.name for c in model.__table__.columns}
            filtered_dict = {k: v for k, v in record_dict.items() if k in model_columns}
            
            # Merge handles insert or update based on primary key
            db.merge(model(**filtered_dict))
            count += 1
        # Commit is handled by the get_db context manager
        logger.debug(f"Prepared {count} records for upsert into {model.__tablename__}.")
        return count
    except Exception as e:
        logger.error(f"Error during batch upsert for {model.__tablename__}: {e}", exc_info=True)
        # Rollback will be handled by the get_db context manager
        raise

def upsert_users(db: Session, users_data: List[Dict[str, Any]]) -> int:
    """Upserts a batch of transformed user data into the dim_xiaoe_user table."""
    logger.info(f"Upserting {len(users_data)} user records...")
    return _batch_upsert(db, XiaoeUser, users_data)

def upsert_goods(db: Session, goods_data: List[Dict[str, Any]]) -> int:
    """Upserts a batch of transformed goods data into the dim_xiaoe_goods table."""
    logger.info(f"Upserting {len(goods_data)} goods records...")
    return _batch_upsert(db, XiaoeGoods, goods_data)

def upsert_orders(db: Session, orders_data: List[Dict[str, Any]]) -> int:
    """Upserts a batch of transformed order data into the fact_xiaoe_order table."""
    logger.info(f"Upserting {len(orders_data)} order records...")
    return _batch_upsert(db, XiaoeOrder, orders_data)

# --- Item Upsert Functions ---

def upsert_order_items(db: Session, items_data: List[Dict[str, Any]]) -> int:
    """Upserts a batch of order items using MySQL's ON DUPLICATE KEY UPDATE.
    Assumes a unique constraint exists on (order_id, sku_id) or similar.
    If sku_id is missing, the item might be skipped or cause errors depending on DB schema.
    """
    if not items_data:
        return 0

    count = 0
    skipped_no_sku = 0
    insert_stmt = mysql_insert(XiaoeOrderItem)
    
    # Filter out items without sku_id as it's part of our intended unique key
    valid_items_data = []
    for item in items_data:
        if item.get('sku_id'): 
            valid_items_data.append(item)
        else:
            skipped_no_sku += 1
            logger.warning(f"Skipping order item insert for order_id {item.get('order_id')} because sku_id is missing. Goods: {item.get('goods_name')}")
            
    if not valid_items_data:
        logger.warning(f"No valid order items with sku_id found to upsert (skipped {skipped_no_sku}).")
        return 0

    # Prepare the dictionary for ON DUPLICATE KEY UPDATE
    # Exclude primary key and potentially the unique key columns from update if desired
    update_dict = { 
        col.name: col 
        for col in insert_stmt.inserted 
        if not col.primary_key and col.name not in ['order_id', 'sku_id'] # Don't update the keys themselves
    }

    # If no columns are left to update (e.g., only keys and PK exist), handle appropriately
    if not update_dict:
         logger.warning("No columns specified for update in ON DUPLICATE KEY UPDATE for order items. Check model definition.")
         # Decide strategy: either skip update or update a dummy column like etl_updated_at if available
         # For now, let's proceed assuming there are columns to update.
         # If XiaoeOrderItem only had PK and order_id/sku_id, this logic would need adjustment.
         pass # Or potentially set update_dict manually if needed for a specific driver/DB version

    # Construct the final statement with ON DUPLICATE KEY UPDATE
    # The keys of update_dict are the columns to SET
    # The values (insert_stmt.inserted[col_name]) refer to the values from the INSERT part
    upsert_stmt = insert_stmt.on_duplicate_key_update(update_dict)
    
    try:
        # Execute the upsert statement for valid items
        db.execute(upsert_stmt, valid_items_data) 
        
        # We cannot reliably get rowcount for ON DUPLICATE KEY UPDATE with all drivers/versions.
        # Instead, we report the number of valid items we attempted to process.
        processed_count = len(valid_items_data)
        logger.info(f"Successfully executed upsert for {processed_count} order items. Skipped {skipped_no_sku} items due to missing sku_id.")
        return processed_count # Return number of items processed by this function
    except Exception as e:
        logger.error(f"Error during order item upsert: {e}", exc_info=True)
        # Rollback is handled by get_db
        raise

def upsert_aftersales(db: Session, aftersales_data: List[Dict[str, Any]]) -> int:
    """Upserts a batch of transformed aftersale data into the fact_xiaoe_aftersale table."""
    logger.info(f"Upserting {len(aftersales_data)} aftersale records...")
    return _batch_upsert(db, XiaoeAftersale, aftersales_data)

def upsert_aftersale_items(db: Session, items_data: List[Dict[str, Any]]) -> int:
    """Handles inserting aftersale items using a delete-then-insert strategy
    based on the aftersale_id.
    """
    if not items_data:
        return 0

    # 1. Get unique aftersale_ids from the batch
    aftersale_ids = {item['aftersale_id'] for item in items_data if 'aftersale_id' in item}
    if not aftersale_ids:
        logger.warning("No aftersale_ids found in the items data batch. Cannot proceed with delete/insert.")
        return 0

    try:
        # 2. Delete existing items for these aftersale_ids
        delete_stmt = delete(XiaoeAftersaleItem).where(XiaoeAftersaleItem.aftersale_id.in_(aftersale_ids))
        delete_result = db.execute(delete_stmt)
        logger.debug(f"Deleted {delete_result.rowcount} existing aftersale items for {len(aftersale_ids)} aftersale IDs.")

        # 3. Bulk insert the new items
        # Ensure dictionaries only contain columns present in the model
        model_columns = {c.name for c in XiaoeAftersaleItem.__table__.columns if not c.primary_key}
        filtered_items_data = [
            {k: v for k, v in item_dict.items() if k in model_columns} 
            for item_dict in items_data
        ]

        if filtered_items_data:        
            insert_stmt = insert(XiaoeAftersaleItem)
            insert_result = db.execute(insert_stmt, filtered_items_data)
            logger.info(f"Successfully inserted {len(filtered_items_data)} new aftersale items (DB reported rows affected: {insert_result.rowcount}).")
            return len(filtered_items_data) # Return number of items inserted
        else:
            logger.info("No valid aftersale items remained after filtering for insertion.")
            return 0
            
    except Exception as e:
        logger.error(f"Error during aftersale item delete/insert: {e}", exc_info=True)
        # Rollback is handled by get_db
        raise

# --- Sync State Management Functions ---

def get_sync_state(db: Session, sync_type: str) -> Optional[SyncState]:
    """Retrieves the sync state record for a given sync type."""
    try:
        state = db.query(SyncState).filter(SyncState.sync_type == sync_type).first()
        if state:
            logger.debug(f"Retrieved sync state for '{sync_type}': {state}")
        else:
            logger.info(f"No existing sync state found for '{sync_type}'. Will start from beginning.")
        return state
    except Exception as e:
        logger.error(f"Error retrieving sync state for '{sync_type}': {e}", exc_info=True)
        return None

def update_sync_state(db: Session, sync_type: str, **kwargs):
    """Updates or creates the sync state record for a given sync type."""
    kwargs['last_updated_at'] = datetime.datetime.now()
    
    try:
        existing_state = db.query(SyncState).filter(SyncState.sync_type == sync_type).first()
        
        if existing_state:
            # Use SQLAlchemy ORM update approach which is generally safer
            for key, value in kwargs.items():
                setattr(existing_state, key, value)
            logger.debug(f"Updating sync state for '{sync_type}'. Values: {kwargs}")
            # ORM object is automatically part of the session's transaction
        else:
            # Insert new record
            kwargs['sync_type'] = sync_type
            new_state = SyncState(**kwargs)
            db.add(new_state)
            logger.info(f"Creating new sync state for '{sync_type}'. Values: {kwargs}")
            
        # Flush changes to DB within the current transaction managed by get_db
        db.flush()
        logger.debug(f"Flushed session after updating/creating sync state for '{sync_type}'.")

    except Exception as e:
        logger.error(f"Error updating/creating sync state for '{sync_type}': {e}", exc_info=True)
        raise
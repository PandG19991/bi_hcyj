# Main script for coordinating data synchronization

import time
import datetime
import json # Keep json import if needed elsewhere, or remove if only for samples
import os # Import os module
from dotenv import load_dotenv # Make sure load_dotenv is imported
from src.xiaoe.client import XiaoeClient, XiaoeError
from src.core.logger import logger, setup_logger
# Import transformer functions
from src.core.transformers import (
    transform_user, 
    transform_order, 
    transform_aftersale, 
    transform_goods
)
# Import database manager functions
from src.database.manager import (
    get_db, 
    upsert_users, 
    upsert_goods, 
    upsert_orders, 
    upsert_order_items,
    upsert_aftersales,
    upsert_aftersale_items
)


def sync_xiaoe_users():
    """Fetches user data, transforms, and upserts. Limited to 10 pages for testing."""
    logger.info("Starting Xiaoe user synchronization (limited to 10 pages for testing)...")
    total_processed = 0
    total_upserted = 0
    page_count = 0
    es_skip = None # Start with no cursor for the first page
    page_size = 50
    max_pages_to_fetch = 10 # Restored page limit variable

    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully.")

        while True: 
            page_count += 1
            
            # === Test Limit Check ===
            if page_count > max_pages_to_fetch: # Restored limit check block
                logger.info(f"Reached the test limit of {max_pages_to_fetch} pages for user sync. Stopping user sync.") # Restored log
                break
            # =======================

            logger.info(f"Attempting to fetch user page {page_count}/{max_pages_to_fetch} (page_size={page_size})...") # Restored log
            
            user_data = client.get_users_list(page_size=page_size, es_skip=es_skip)
            user_list = user_data.get('list', [])
            total_api_reported = user_data.get('total', 0) 
            batch_size = len(user_list)
            total_processed += batch_size 
            logger.info(f"Fetched page {page_count}: {batch_size} users retrieved. Total processed so far: {total_processed}. API total: {total_api_reported}")

            if not user_list:
                logger.info("Received empty user list, assuming end of data.")
                break # Exit loop if no more users are returned

            # --- Processing Batch ---            
            logger.debug(f"Transforming batch of {batch_size} users for page {page_count}...")
            transformed_users = []
            for raw_user in user_list:
                transformed = transform_user(raw_user)
                if transformed:
                    transformed_users.append(transformed)
                    logger.debug(f"Successfully transformed user ID: {transformed.get('user_id')}")
                else:
                    logger.warning(f"Failed to transform user record: {raw_user.get('user_id')}")
            
            if transformed_users:
                 try:
                     with get_db() as db:
                         upserted_count = upsert_users(db, transformed_users)
                         total_upserted += upserted_count
                         logger.info(f"Successfully upserted {upserted_count} users for page {page_count}.")
                 except Exception as db_err:
                     logger.error(f"Database error during user upsert for page {page_count}: {db_err}", exc_info=True)
                     # Decide if we should stop or continue on DB error
                     # For now, let's stop if DB fails
                     raise
            
            logger.debug(f"Finished processing batch for page {page_count}.")
            # ------------------------

            # --- Get next cursor --- 
            if user_list: # Check again, though should be redundant with the break above
                last_user = user_list[-1]
                next_es_skip = last_user.get('es_skip') 
                if next_es_skip:
                    es_skip = next_es_skip
                    logger.debug(f"Obtained next es_skip cursor.") # Simplified log
                else:
                    logger.warning("Could not find 'es_skip' key in the last user object. Assuming end of data or API change.")
                    break
            else:
                 # This case should ideally not be reached due to the earlier break
                 logger.info("User list became empty, stopping pagination.")
                 break
                 
            time.sleep(0.1) # Keep optional delay

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during user sync (page {page_count}): Code={e.code}, Message={e.message}, Details={e.details}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe user sync (page {page_count}): {e}", exc_info=True)

    # Corrected final log message to reflect actual pages fetched
    final_page_count = page_count -1 if page_count > 0 else 0
    logger.info(f"Xiaoe user synchronization process finished (limited to {final_page_count} pages fetched). Total users processed: {total_processed}. Total users upserted: {total_upserted}.")


def sync_xiaoe_orders(days_back=1):
    """Fetches recent order data from Xiaoe API using pagination and processes batches."""
    logger.info(f"Starting Xiaoe order synchronization for the last {days_back} day(s)...")
    total_processed = 0
    total_orders_upserted = 0
    total_items_processed = 0 # Track items separately
    page_count = 0
    current_page = 1 
    page_size = 50 # Restore original page size

    # Calculate time range
    end_time_dt = datetime.datetime.now()
    start_time_dt = end_time_dt - datetime.timedelta(days=days_back)
    start_time_str = start_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    search_type = 3 # 3: update_time

    logger.info(f"Fetching orders updated between {start_time_str} and {end_time_str}")

    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for order sync.")

        while True: # Restore loop for pagination
            page_count += 1
            logger.info(f"Attempting to fetch order page {current_page} (page_size={page_size})...")

            order_data = client.get_order_list(
                search_type=search_type,
                start_time=start_time_str,
                end_time=end_time_str,
                page=current_page,
                page_size=page_size
            )

            order_list = order_data.get('list', [])
            total_api_reported = order_data.get('total', 0)
            batch_size = len(order_list)
            total_processed += batch_size
            logger.info(f"Fetched page {current_page}: {batch_size} orders retrieved. Total processed so far: {total_processed}. API total for time range: {total_api_reported}")

            if not order_list:
                logger.info(f"Received empty order list on page {current_page}, assuming end of data for this time range.")
                break 

            # --- Processing Batch ---            
            logger.debug(f"Transforming batch of {batch_size} orders for page {current_page}...")
            transformed_orders = []
            transformed_order_items = [] # Collect items separately if storing in own table
            for raw_order in order_list:
                transformed = transform_order(raw_order)
                if transformed:
                    # Separate items before adding order to list
                    items = transformed.pop('order_items', []) 
                    transformed_orders.append(transformed)
                    if items:
                        transformed_order_items.extend(items)
                    logger.debug(f"Successfully transformed order ID: {transformed.get('order_id')}")
                else:
                    logger.warning(f"Failed to transform order record: {raw_order.get('order_info', {}).get('order_id')}")
            
            if transformed_orders:
                try:
                    with get_db() as db: 
                        # Upsert Orders first
                        upserted_orders_count = upsert_orders(db, transformed_orders)
                        total_orders_upserted += upserted_orders_count
                        logger.info(f"Successfully upserted {upserted_orders_count} orders for page {current_page}.")
                        
                        # Flush orders to ensure they exist for FK constraints
                        db.flush() 
                        logger.debug(f"Flushed session after upserting {upserted_orders_count} orders.")

                        # Then handle Order Items
                        if transformed_order_items:
                            processed_items_count = upsert_order_items(db, transformed_order_items)
                            total_items_processed += processed_items_count
                            logger.info(f"Processed {processed_items_count} order items for page {current_page}.")
                        else:
                            logger.info(f"No order items to process for page {current_page}.")
                except Exception as db_err:
                    logger.error(f"Database error during order/item upsert for page {current_page}: {db_err}", exc_info=True)
                    raise # Re-raise to be caught by the outer loop's exception handler
            
            logger.debug(f"Finished processing batch for page {current_page}.")
            # ------------------------

            current_page += 1
            time.sleep(0.1) # Keep optional delay

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during order sync (page {current_page}): Code={e.code}, Message={e.message}, Details={e.details}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe order sync (page {current_page}): {e}", exc_info=True)

    logger.info(f"Xiaoe order synchronization process finished. Total pages fetched: {page_count}. Total orders processed: {total_processed}. Orders upserted: {total_orders_upserted}. Items processed: {total_items_processed}.")


def sync_xiaoe_aftersales(days_back=1):
    """Fetches recent aftersale order data from Xiaoe API using pagination and processes batches."""
    logger.info(f"Starting Xiaoe aftersale synchronization for the last {days_back} day(s)...")
    total_processed = 0
    total_aftersales_upserted = 0
    total_items_processed = 0
    page_count = 0
    current_page_index = 1 
    page_size = 50 # Restore original page size

    # Calculate time range
    end_time_dt = datetime.datetime.now()
    start_time_dt = end_time_dt - datetime.timedelta(days=days_back)
    start_date_str = start_time_dt.strftime("%Y-%m-%d") 
    end_date_str = end_time_dt.strftime("%Y-%m-%d")
    created_at_range = f"{start_date_str}||{end_date_str}"
    date_type = "created_at" 

    logger.info(f"Fetching aftersales using {date_type} between {start_date_str} and {end_date_str}")

    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for aftersale sync.")

        while True: # Restore loop for pagination
            page_count += 1 
            logger.info(f"Attempting to fetch aftersale page index {current_page_index} (page_size={page_size})...")

            aftersale_data = client.get_aftersale_list(
                page_index=current_page_index,
                page_size=page_size,
                date_type=date_type, 
                created_at=created_at_range 
            )

            aftersale_list = aftersale_data.get('list', [])
            total_api_reported = aftersale_data.get('row_count', 0) 
            batch_size = len(aftersale_list)
            total_processed += batch_size
            logger.info(f"Fetched page index {current_page_index}: {batch_size} aftersales retrieved. Total processed so far: {total_processed}. API total for time range: {total_api_reported}")

            if not aftersale_list:
                logger.info(f"Received empty aftersale list on page index {current_page_index}, assuming end of data for this time range.")
                break 

            # --- Processing Batch ---            
            logger.debug(f"Transforming batch of {batch_size} aftersales for page index {current_page_index}...")
            transformed_aftersales = []
            transformed_aftersale_items = []
            for raw_aftersale in aftersale_list:
                transformed = transform_aftersale(raw_aftersale)
                if transformed:
                    items = transformed.pop('aftersale_items', [])
                    transformed_aftersales.append(transformed)
                    if items:
                        transformed_aftersale_items.extend(items)
                    logger.debug(f"Successfully transformed aftersale ID: {transformed.get('aftersale_id')}")
                else:
                    logger.warning(f"Failed to transform aftersale record: {raw_aftersale.get('aftersale_id')}")
            
            if transformed_aftersales:
                 try:
                     with get_db() as db:
                         # Upsert Aftersales first
                         upserted_count = upsert_aftersales(db, transformed_aftersales)
                         total_aftersales_upserted += upserted_count
                         logger.info(f"Successfully upserted {upserted_count} aftersales for page {current_page_index}.")
                         
                         # Flush aftersales to ensure they exist for FK constraints
                         db.flush()
                         logger.debug(f"Flushed session after upserting {upserted_count} aftersales.")

                         # Then handle Aftersale Items
                         if transformed_aftersale_items:
                             processed_items_count = upsert_aftersale_items(db, transformed_aftersale_items)
                             total_items_processed += processed_items_count
                             logger.info(f"Processed {processed_items_count} aftersale items for page {current_page_index}.")
                         else:
                            logger.info(f"No aftersale items to process for page {current_page_index}.")
                 except Exception as db_err:
                     logger.error(f"Database error during aftersale/item upsert for page {current_page_index}: {db_err}", exc_info=True)
                     raise # Re-raise to be caught by the outer loop's exception handler

            logger.debug(f"Finished processing batch for page index {current_page_index}.")
            # ------------------------

            current_page_index += 1
            time.sleep(0.1)

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during aftersale sync (page index {current_page_index}): Code={e.code}, Message={e.message}, Details={e.details}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe aftersale sync (page index {current_page_index}): {e}", exc_info=True)

    logger.info(f"Xiaoe aftersale synchronization process finished. Total pages fetched: {page_count}. Total aftersales processed: {total_processed}. Aftersales upserted: {total_aftersales_upserted}. Items processed: {total_items_processed}.")


def sync_xiaoe_goods():
    """Fetches goods list data from Xiaoe API using pagination and processes batches."""
    logger.info(f"Starting Xiaoe goods list synchronization...")
    total_processed = 0
    total_upserted = 0
    page_count = 0
    current_page = 1 
    page_size = 50 # Restore page size

    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for goods sync.")

        while True: # Restore loop for pagination
            page_count += 1 
            logger.info(f"Attempting to fetch goods list page {current_page} (page_size={page_size})...")

            goods_data = client.get_goods_list(
                page=current_page,
                page_size=page_size
            )

            goods_list = goods_data.get('list', [])
            total_api_reported = goods_data.get('total', 0)
            api_current_page = goods_data.get('current_page', current_page) 
            batch_size = len(goods_list)
            total_processed += batch_size
            logger.info(f"Fetched page {api_current_page}: {batch_size} goods retrieved. Total processed so far: {total_processed}. API total: {total_api_reported}")

            if not goods_list:
                logger.info(f"Received empty goods list on page {api_current_page}, assuming end of data.")
                break 

            # --- Processing Batch ---            
            logger.debug(f"Transforming batch of {batch_size} goods for page {api_current_page}...")
            transformed_goods = []
            for raw_goods in goods_list:
                transformed = transform_goods(raw_goods)
                if transformed:
                    transformed_goods.append(transformed)
                    logger.debug(f"Successfully transformed goods resource ID: {transformed.get('goods_resource_id')}")
                else:
                    logger.warning(f"Failed to transform goods record: {raw_goods.get('resource_id')}")
            
            if transformed_goods:
                 try:
                     with get_db() as db:
                         upserted_count = upsert_goods(db, transformed_goods)
                         total_upserted += upserted_count
                         logger.info(f"Successfully upserted {upserted_count} goods for page {api_current_page}.")
                 except Exception as db_err:
                     logger.error(f"Database error during goods upsert for page {api_current_page}: {db_err}", exc_info=True)
                     raise

            logger.debug(f"Finished processing batch for page {api_current_page}.")
            # ------------------------

            current_page += 1
            time.sleep(0.1)

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during goods sync (page {current_page}): Code={e.code}, Message={e.message}, Details={e.details}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe goods sync (page {current_page}): {e}", exc_info=True)

    logger.info(f"Xiaoe goods list synchronization process finished. Total pages fetched: {page_count}. Total goods processed: {total_processed}. Total goods upserted: {total_upserted}.")


# --- Main Execution ---

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv() 
    
    # Setup logger 
    # Now setup_logger uses settings.LOG_LEVEL by default, 
    # but we can override it here if needed for this run.
    # We pass the log_file argument.
    setup_logger(log_level_str="DEBUG", log_file="sync.log") 
    
    # Read configuration from environment variables with defaults
    try:
        orders_days_back = int(os.getenv("SYNC_ORDERS_DAYS_BACK", 1))
    except (ValueError, TypeError):
        logger.warning("Invalid or missing SYNC_ORDERS_DAYS_BACK env variable, defaulting to 1.")
        orders_days_back = 1
    
    try:
        aftersales_days_back = int(os.getenv("SYNC_AFTERSALES_DAYS_BACK", 1))
    except (ValueError, TypeError):
        logger.warning("Invalid or missing SYNC_AFTERSALES_DAYS_BACK env variable, defaulting to 1.")
        aftersales_days_back = 1

    # Initialize database tables
    try:
        from src.database.manager import create_all_tables
        logger.info("Initializing database tables if they don't exist...")
        create_all_tables() 
        logger.info("Database table initialization check complete.")
    except Exception as init_db_err:
        logger.critical(f"Failed to initialize database tables: {init_db_err}", exc_info=True)
        exit(1) 
        
    logger.info("Starting data synchronization overall process...")
    
    # Call sync functions sequentially, using configured days_back
    sync_functions = [
        ("Users", sync_xiaoe_users),
        ("Orders", lambda: sync_xiaoe_orders(days_back=orders_days_back)), # Use variable
        ("Aftersales", lambda: sync_xiaoe_aftersales(days_back=aftersales_days_back)), # Use variable
        ("Goods", sync_xiaoe_goods)
    ]

    overall_success = True
    for name, sync_func in sync_functions:
        try:
            logger.info(f"--- Running {name} Synchronization --- ")
            sync_func()
            logger.info(f"--- Finished {name} Synchronization Successfully ---")
        except Exception as sync_err:
            logger.error(f"!!! Error during {name} Synchronization: {sync_err}", exc_info=True)
            logger.error(f"--- {name} Synchronization FAILED, continuing with next task --- ")
            overall_success = False # Mark that at least one task failed
            
    logger.info("Data synchronization overall process finished.")
    if not overall_success:
        logger.warning("One or more synchronization tasks failed. Please check the logs above for details.") 
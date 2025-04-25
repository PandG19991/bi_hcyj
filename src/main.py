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
    upsert_aftersale_items,
    get_sync_state,
    update_sync_state
)
from src.database.models import XiaoeAftersale, XiaoeAftersaleItem, XiaoeOrder
from sqlalchemy.exc import IntegrityError


def sync_xiaoe_users():
    """Fetches user data incrementally using es_skip cursor and upserts (limited for testing)."""
    sync_type = 'users'
    logger.info(f"Starting incremental Xiaoe user synchronization (limited to 10 pages)...")
    total_processed = 0
    total_upserted = 0
    page_count = 0
    es_skip = None
    page_size = 50 # Increased page size
    # max_pages_to_fetch = 20 # Reduced page limit # REMOVED PAGE LIMIT

    # --- Get initial state ---
    try:
        with get_db() as db:
            initial_state = get_sync_state(db, sync_type)
            if initial_state and initial_state.last_processed_cursor:
                es_skip = initial_state.last_processed_cursor
                logger.info(f"Resuming user sync from previous cursor: {es_skip}")
            else:
                logger.info("No previous user sync cursor found. Starting from the beginning.")
    except Exception as e:
        logger.error(f"Failed to retrieve initial sync state for {sync_type}. Starting full sync. Error: {e}", exc_info=True)
        # Proceed with es_skip = None

    # --- Main Sync Loop ---
    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for user sync.")

        while True:
            # === REMOVED Test Limit Check ===
            # if page_count >= max_pages_to_fetch: # Use >= to fetch exactly 10 pages (1 to 10)
            #     logger.info(f"Reached the test limit of {max_pages_to_fetch} pages for user sync. Stopping.")
            #     break
            # =======================

            page_count += 1
            # Adjusted log message
            logger.info(f"Attempting to fetch user page {page_count} (page_size={page_size}). Cursor: {es_skip}")

            # Fetch data using the current es_skip
            user_data = client.get_users_list(page_size=page_size, es_skip=es_skip)
            user_list = user_data.get('list', [])
            total_api_reported = user_data.get('total', 0) # Note: total might not be accurate with cursor
            batch_size = len(user_list)
            total_processed += batch_size
            logger.info(f"Fetched page {page_count}: {batch_size} users retrieved. Total processed this run: {total_processed}.")

            if not user_list:
                logger.info("Received empty user list, assuming end of data.")
                # Successfully reached the end, mark as success before breaking
                # (Status update will be handled in the main execution block)
                break

            # --- Processing Batch ---
            logger.debug(f"Transforming batch of {batch_size} users for page {page_count}...")
            transformed_users = []
            for raw_user in user_list:
                transformed = transform_user(raw_user)
                if transformed:
                    transformed_users.append(transformed)
                else:
                    logger.warning(f"Failed to transform user record: {raw_user.get('user_id')}")

            next_es_skip = None # Reset for safety
            if user_list: # Get the cursor for the *next* request *before* potential DB error
                last_user = user_list[-1]
                next_es_skip = last_user.get('es_skip')
                if not next_es_skip:
                    logger.warning("Could not find 'es_skip' key in the last user object of the current batch. Stopping sync.")
                    # Treat this as reaching the end, but don't update the cursor state for this incomplete batch
                    break

            if transformed_users:
                try:
                    with get_db() as db:
                        upserted_count = upsert_users(db, transformed_users)
                        total_upserted += upserted_count
                        logger.info(f"Successfully upserted {upserted_count} users for page {page_count}.")

                        # --- Update State After Successful Batch ---
                        if next_es_skip:
                            update_sync_state(db, sync_type, last_processed_cursor=next_es_skip)
                            logger.info(f"Successfully updated sync state cursor for {sync_type} after page {page_count}.")
                        else:
                             # Should not happen if break condition above works, but log just in case
                             logger.warning(f"Skipping state update for {sync_type} page {page_count} due to missing next cursor.")
                        # ------------------------------------------

                except Exception as db_err:
                    logger.error(f"Database error during user upsert for page {page_count}. Stopping sync. Error: {db_err}", exc_info=True)
                    # Don't update state, re-raise to mark task as failed
                    raise

            logger.debug(f"Finished processing batch for page {page_count}.")
            # ------------------------

            # Prepare for the next iteration
            es_skip = next_es_skip # Use the cursor obtained before the DB operation

            if not es_skip: # Should be redundant if break worked
                 logger.warning("Stopping user sync because next cursor is missing.")
                 break

            time.sleep(0.1) # Keep optional delay

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during user sync (page {page_count}): Code={e.code}, Message={e.message}. Stopping sync.", exc_info=True)
        raise # Re-raise to mark task as failed
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe user sync (page {page_count}). Stopping sync. Error: {e}", exc_info=True)
        raise # Re-raise to mark task as failed

    # Final log reflects this specific run
    logger.info(f"Xiaoe user synchronization attempt finished. Users processed this run: {total_processed}. Users upserted: {total_upserted}.")
    # Overall success/failure status logged in main block


def sync_xiaoe_orders(days_back=1):
    """Fetches order data incrementally based on updated_at timestamp (limited for testing)."""
    sync_type = 'orders'
    logger.info(f"Starting incremental Xiaoe order synchronization (limited to 10 pages)...")
    total_processed = 0
    total_orders_upserted = 0
    total_items_processed = 0
    page_count = 0
    current_page = 1
    page_size = 50 # Increased page size
    run_max_timestamp = None
    # max_pages_to_fetch = 20 # Reduced page limit # REMOVED PAGE LIMIT

    # Calculate time range - RESTORED ORIGINAL LOGIC
    end_time_dt = datetime.datetime.now()
    start_time_dt = end_time_dt - datetime.timedelta(days=days_back)
    start_time_str = start_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    search_type = 3 # 3: update_time

    logger.info(f"Fetching orders updated between {start_time_str} and {end_time_str} (Based on days_back={days_back})")

    # --- Main Sync Loop ---
    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for order sync.")

        while True:
            # === REMOVED Test Limit Check ===
            # if page_count >= max_pages_to_fetch:
            #     logger.info(f"Reached the test limit of {max_pages_to_fetch} pages for order sync. Stopping.")
            #     break
            # =======================

            page_count += 1
            # Adjusted log message to remove max_pages reference
            logger.info(f"Attempting to fetch order page {current_page} (Run page {page_count}, page_size={page_size}) for time range...")

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
                    raise # Re-raise to ensure the task is marked as failed
            
            logger.debug(f"Finished processing batch for page {current_page}.")
            # ------------------------

            current_page += 1
            time.sleep(0.1) # Keep optional delay

        # --- Update Final State After Successful Run (or hitting limit) ---
        if run_max_timestamp:
            try:
                with get_db() as db:
                    update_sync_state(db, sync_type, last_processed_timestamp=run_max_timestamp, last_run_status='in_progress')
                    logger.info(f"Successfully updated final sync state timestamp for {sync_type} to {run_max_timestamp.strftime('%Y-%m-%d %H:%M:%S')}.")
            except Exception as state_err:
                 logger.error(f"Failed to update final sync state for {sync_type} after successful run. Error: {state_err}", exc_info=True)

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during order sync (page {current_page}): Code={e.code}, Message={e.message}, Details={e.details}. Stopping sync.", exc_info=True)
        raise # Re-raise to mark task as failed
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe order sync (page {current_page}): {e}. Stopping sync.", exc_info=True)
        raise # Re-raise to mark task as failed

    logger.info(f"Xiaoe order synchronization attempt finished. Orders processed this run: {total_processed}. Orders upserted: {total_orders_upserted}. Items processed: {total_items_processed}.")
    # Overall success/failure status logged in main block


def sync_xiaoe_aftersales(days_back=1):
    """Fetches aftersale data incrementally based on updated_at timestamp (limited for testing)."""
    sync_type = 'aftersales'
    logger.info(f"Starting incremental Xiaoe aftersale synchronization (limited to 10 pages)...")
    total_processed = 0
    total_aftersales_upserted = 0
    total_items_processed = 0
    page_count = 0
    current_page_index = 1
    page_size = 50
    run_max_timestamp = None
    # max_pages_to_fetch = 20 # Reduced page limit

    # --- Determine Time Range --- RESTORED ORIGINAL LOGIC
    start_time_dt = None
    end_time_dt = datetime.datetime.now() # Always sync up to now
    try:
        with get_db() as db:
            initial_state = get_sync_state(db, sync_type)
            if initial_state and initial_state.last_processed_timestamp:
                start_time_dt = initial_state.last_processed_timestamp
                logger.info(f"Resuming aftersale sync from last processed timestamp: {start_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                start_time_dt = end_time_dt - datetime.timedelta(days=days_back)
                logger.info(f"No previous aftersale sync timestamp found. Starting from {days_back} day(s) ago: {start_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"Failed to retrieve initial sync state for {sync_type}. Falling back to {days_back} days back. Error: {e}", exc_info=True)
        start_time_dt = end_time_dt - datetime.timedelta(days=days_back)

    start_time_str = start_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    time_range_str = f"{start_time_str}||{end_time_str}"
    date_type = "updated_at" # Use the string identifier as per docs

    logger.info(f"Fetching aftersales updated between {start_time_str} and {end_time_str} (using date_type='{date_type}')")

    # --- Main Sync Loop ---
    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for aftersale sync.")

        while True:
            # === REMOVED Test Limit Check ===
            # if page_count >= max_pages_to_fetch:
            #     logger.info(f"Reached the test limit of {max_pages_to_fetch} pages for aftersale sync. Stopping.")
            #     break
            # =======================

            page_count += 1
            # Adjusted log message
            logger.info(f"Attempting to fetch aftersale page index {current_page_index} (Run page {page_count}, page_size={page_size}) for time range...")

            # Adjust API call based on documentation
            aftersale_data = client.get_aftersale_list(
                page_index=current_page_index,
                page_size=page_size,
                date_type=date_type,       # Specify the field to filter on ('updated_at')
                created_at=time_range_str  # Pass the time range string via 'created_at'
            )

            aftersale_list = aftersale_data.get('list', [])
            total_api_reported = aftersale_data.get('row_count', 0)
            batch_size = len(aftersale_list)
            total_processed += batch_size
            logger.info(f"Fetched page index {current_page_index}: {batch_size} aftersales retrieved. Total processed this run: {total_processed}. API total for time range: {total_api_reported}")

            if not aftersale_list:
                logger.info(f"Received empty aftersale list on page index {current_page_index}, assuming end of data for this time range.")
                break

            # --- Processing Batch --- RESTORED BATCH LOGIC ---
            if transformed_aftersales:
                try:
                    with get_db() as db:
                        # Restore batch upsert for aftersales
                        upserted_count = upsert_aftersales(db, transformed_aftersales)
                        total_aftersales_upserted += upserted_count
                        logger.info(f"Attempted to upsert {len(transformed_aftersales)} aftersales for page {current_page_index}. Upserted count: {upserted_count}.")

                        db.flush() # Flush aftersales before items
                        logger.debug(f"Flushed session after upserting aftersales for page {current_page_index}.")

                        # Restore batch upsert for items
                        if transformed_aftersale_items:
                            processed_items_count = upsert_aftersale_items(db, transformed_aftersale_items)
                            total_items_processed += processed_items_count
                            logger.info(f"Processed {processed_items_count} aftersale items for page {current_page_index}.")
                        else:
                            logger.info(f"No aftersale items to process for page {current_page_index}.")

                        # DO NOT update timestamp state here - done at the end

                except Exception as db_err:
                    # Log the error and re-raise to fail the task
                    logger.error(f"Database error during batch aftersale/item upsert for page {current_page_index}. Stopping sync. Error: {db_err}", exc_info=True)
                    raise # Re-raise to mark task as failed

            # --- REMOVED Individual Processing Block ---

            logger.debug(f"Finished processing batch for page index {current_page_index}.")
            # ------------------------

            current_page_index += 1
            time.sleep(0.1)

        # --- Update Final State After Loop Finishes (or hits limit/error) ---
        # Update timestamp ONLY if the loop finished without being stopped by an error
        # The main loop exception handling will set the final status (success/failed)
        if run_max_timestamp:
            try:
                with get_db() as db:
                    # Don't set status here, just update timestamp if loop completed
                    update_sync_state(db, sync_type, last_processed_timestamp=run_max_timestamp)
                    logger.info(f"Successfully updated final sync state timestamp for {sync_type} to {run_max_timestamp.strftime('%Y-%m-%d %H:%M:%S')}.")
            except Exception as state_err:
                 logger.error(f"Failed to update final sync state timestamp for {sync_type} after run. Error: {state_err}", exc_info=True)

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during aftersale sync (page index {current_page_index}): Code={e.code}, Message={e.message}. Stopping sync.", exc_info=True)
        raise # Re-raise API errors to mark task as failed
    except Exception as e:
        # This will catch unexpected errors *outside* the inner DB loop (like client init)
        # or fatal DB errors re-raised from the inner loop.
        logger.error(f"An UNEXPECTED/FATAL error occurred during Xiaoe aftersale sync (page index {current_page_index}). Stopping sync. Error: {e}", exc_info=True)
        raise # Re-raise other fatal errors

    # Adjusted final log message to remove page limit reference and reflect batch processing success metric
    logger.info(f"Xiaoe aftersale synchronization attempt finished. Aftersales processed (API): {total_processed}. Aftersales upserted (DB): {total_aftersales_upserted}. Items processed (DB): {total_items_processed}.")
    # The main loop will still mark the overall job status based on whether an exception was raised here.


def sync_xiaoe_goods():
    """Fetches goods list data incrementally using page number and upserts (limited for testing)."""
    sync_type = 'goods'
    logger.info(f"Starting incremental Xiaoe goods list synchronization (limited to 10 pages)...")
    total_processed = 0
    total_upserted = 0
    page_count = 0 # Tracks pages fetched *this run*
    current_page = 1 # Page number to request from API
    page_size = 100 # Set back to API max limit
    start_page = 1 # Initialize start page
    # max_pages_to_fetch = 20 # Reduced page limit # REMOVED PAGE LIMIT

    # --- Get initial state ---
    try:
        with get_db() as db:
            initial_state = get_sync_state(db, sync_type)
            if initial_state and initial_state.last_processed_page:
                # Important: Check if the last run failed. If so, retry the last known page.
                # Otherwise, start from the next page.
                if initial_state.last_run_status == 'failed':
                     start_page = initial_state.last_processed_page
                     logger.warning(f"Previous goods sync failed at page {start_page}. Retrying from this page.")
                else:
                    start_page = initial_state.last_processed_page + 1
                    logger.info(f"Resuming goods sync from page {start_page} (last processed: {initial_state.last_processed_page}).")
            else:
                logger.info("No previous goods sync page found or last state invalid. Starting from page 1.")
    except Exception as e:
        logger.error(f"Failed to retrieve initial sync state for {sync_type}. Starting full sync from page 1. Error: {e}", exc_info=True)
        # Proceed with start_page = 1

    current_page = start_page # Set the starting page for the loop

    # --- Main Sync Loop ---
    try:
        client = XiaoeClient()
        logger.info("XiaoeClient initialized successfully for goods sync.")

        while True:
            # === REMOVED Test Limit Check (Based on pages fetched *this run*) ===
            # if page_count >= max_pages_to_fetch:
            #     logger.info(f"Reached the test limit of {max_pages_to_fetch} pages for goods sync. Stopping.")
            #     break
            # =======================

            # Note: page_count tracks pages attempted *in this run* starting from 1
            # current_page tracks the actual API page number being requested
            page_count += 1
            # Adjusted log message
            logger.info(f"Attempting to fetch goods list page {current_page} (Run page {page_count}, page_size={page_size})...")

            goods_data = client.get_goods_list(
                page=current_page,
                page_size=page_size
            )

            goods_list = goods_data.get('list', [])
            total_api_reported = goods_data.get('total', 0)
            api_current_page = goods_data.get('current_page', current_page) # Use API reported page if available
            batch_size = len(goods_list)
            total_processed += batch_size
            logger.info(f"Fetched page {api_current_page}: {batch_size} goods retrieved. Total processed this run: {total_processed}. API total: {total_api_reported}")

            if not goods_list:
                logger.info(f"Received empty goods list on page {api_current_page}, assuming end of data.")
                # Successfully reached the end
                break

            # --- Processing Batch ---
            logger.debug(f"Transforming batch of {batch_size} goods for page {api_current_page}...")
            transformed_goods = []
            for raw_goods in goods_list:
                transformed = transform_goods(raw_goods)
                if transformed:
                    transformed_goods.append(transformed)
                else:
                    logger.warning(f"Failed to transform goods record: {raw_goods.get('resource_id')}")

            if transformed_goods:
                try:
                    with get_db() as db:
                        upserted_count = upsert_goods(db, transformed_goods)
                        total_upserted += upserted_count
                        logger.info(f"Successfully upserted {upserted_count} goods for page {api_current_page}.")

                        # --- Update State After Successful Page ---
                        # Update the state with the page number we just successfully processed
                        update_sync_state(db, sync_type, last_processed_page=api_current_page, last_run_status='in_progress') # Mark page success
                        logger.info(f"Successfully updated sync state page for {sync_type} to {api_current_page}.")
                        # -----------------------------------------

                except Exception as db_err:
                    logger.error(f"Database error during goods upsert for page {api_current_page}. Stopping sync. Error: {db_err}", exc_info=True)
                    # Don't update state to this page number, re-raise
                    raise # Re-raise to mark task as failed

            logger.debug(f"Finished processing batch for page {api_current_page}.")
            # ------------------------

            current_page += 1 # Move to the next page for the next iteration
            time.sleep(0.1)

    except XiaoeError as e:
        logger.error(f"Xiaoe API Error during goods sync (page {current_page}): Code={e.code}, Message={e.message}. Stopping sync.", exc_info=True)
        raise # Re-raise to mark task as failed
    except Exception as e:
        logger.error(f"An unexpected error occurred during Xiaoe goods sync (page {current_page}). Stopping sync. Error: {e}", exc_info=True)
        raise # Re-raise to mark task as failed

    # Final log reflects this specific run
    logger.info(f"Xiaoe goods list synchronization attempt finished. Goods processed this run: {total_processed}. Goods upserted: {total_upserted}.")
    # Overall success/failure status logged in main block


# --- Main Execution ---

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Setup logger
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

    # Define sync tasks with their type names for state management
    sync_tasks = [
        {'name': "Users", 'type': 'users', 'func': sync_xiaoe_users},
        {'name': "Orders", 'type': 'orders', 'func': lambda: sync_xiaoe_orders(days_back=orders_days_back)},
        {'name': "Aftersales", 'type': 'aftersales', 'func': lambda: sync_xiaoe_aftersales(days_back=aftersales_days_back)},
        {'name': "Goods", 'type': 'goods', 'func': sync_xiaoe_goods}
    ]

    overall_success = True
    for task in sync_tasks:
        task_name = task['name']
        task_type = task['type']
        sync_func = task['func']
        task_status = 'failed' # Default to failed unless explicitly successful

        try:
            logger.info(f"--- Running {task_name} Synchronization --- ")
            # Optionally mark as 'running' at the start
            # with get_db() as db:
            #     update_sync_state(db, task_type, last_run_status='running')

            sync_func() # Execute the sync function

            # If no exception occurred, mark as success
            task_status = 'success'
            logger.info(f"--- Finished {task_name} Synchronization Successfully --- ") # Added space

        except Exception as sync_err:
            logger.error(f"!!! Error during {task_name} Synchronization: {sync_err}", exc_info=True)
            logger.error(f"--- {task_name} Synchronization FAILED --- ")
            overall_success = False
            # task_status remains 'failed'

        finally:
            # Update the final status in the sync_state table
            try:
                with get_db() as db:
                    # Note: We update status regardless of success/failure of the task itself.
                    # The specific timestamp/page/cursor updates happen *within* the sync functions upon *their* success.
                    update_sync_state(db, task_type, last_run_status=task_status)
                    logger.info(f"Updated final run status for {task_name} ({task_type}) to '{task_status}'.")
            except Exception as state_update_err:
                 logger.error(f"!!! CRITICAL: Failed to update final run status for {task_name} ({task_type}) to '{task_status}'. Error: {state_update_err}", exc_info=True)
                 # If updating the status fails, we might have inconsistent state

    logger.info("Data synchronization overall process finished.")
    if not overall_success:
        logger.warning("One or more synchronization tasks failed. Please check the logs above for details.") 
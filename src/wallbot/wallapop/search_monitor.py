import logging
import time
import json
import asyncio
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.wallapop.api_client import WallapopClient
from src.wallbot.telegram.notifications import format_and_send_message
from src.wallbot.config.settings import TELEGRAM_CHAT_ID

# In-memory store for running search tasks
running_tasks = {}

def _item_matches_filters(item, search) -> bool:
    """Checks if an item's title or description matches the search filters."""
    positive_words = [word.strip().lower() for word in search.positive_words.split(',') if word.strip()]
    negative_words = [word.strip().lower() for word in search.negative_words.split(',') if word.strip()]
    
    item_title = item.get('title', '').lower()
    item_description = item.get('description', '').lower()

    logging.debug(f"Checking item {item.get('id')}:")
    logging.debug(f"  Title: {item_title}")
    logging.debug(f"  Description: {item_description}")
    logging.debug(f"  Positive words: {positive_words}")
    logging.debug(f"  Negative words: {negative_words}")
    
    # If there are positive words, all of them must be present in the title.
    if positive_words and not all(word in item_title for word in positive_words):
        logging.info(f"Item {item.get('id')} rejected: title missing positive words.")
        return False

    # If there are negative words, none should be present in the description.
    if negative_words and any(word in item_description for word in negative_words):
        logging.info(f"Item {item.get('id')} rejected: description contains negative words.")
        return False

    logging.debug(f"Item {item.get('id')} matches all filters.")
    return True

async def _execute_search(search, wallapop_client: WallapopClient, db_helper: DBHelper):
    """Executes a single search, finds new items, and sends notifications."""
    logging.info(f"Executing search for URL: {search.url[:70]}...")
    new_items = []
    try:
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(search.url)
        query_params = parse_qs(parsed_url.query)
        search_params_filtered = {k: v[0] for k, v in query_params.items()}

        request_count = 0
        response_json = wallapop_client.search_items_from_web(**search_params_filtered)
        request_count += 1

        page_count = 1
        if response_json:
            meta = response_json.get('meta', {})
            raw_items = response_json.get('data', {}).get('section', {}).get('payload', {}).get('items', [])
            
            logging.info("meta")
            for key, value in meta.items():
                if key != 'next_page':
                    logging.info(f"{key} = {value}")
            logging.info(f"items length: {len(raw_items)}")
            logging.info(f"request count: {request_count}")

            for item in raw_items:
                item_id = item.get("id")
                if item_id and not db_helper.search_result_exists(search.id, item_id):
                    logging.info(f"New item found for search {search.id}: {item_id}")
                    new_items.append(item)

            next_page = response_json.get('meta', {}).get('next_page')
            while next_page and page_count < search.pages:
                page_count += 1
                logging.info(f"Getting page number {page_count} for search {search.id}")
                response_json = wallapop_client.search_items_from_web(next_page=next_page)
                request_count += 1
                if response_json:
                    meta = response_json.get('meta', {})
                    raw_items = response_json.get('data', {}).get('section', {}).get('payload', {}).get('items', [])

                    logging.info("meta")
                    for key, value in meta.items():
                        if key != 'next_page':
                            logging.info(f"{key} = {value}")
                    logging.info(f"items length: {len(raw_items)}")
                    logging.info(f"request count: {request_count}")

                    for item in raw_items:
                        item_id = item.get("id")
                        if item_id and not db_helper.search_result_exists(search.id, item_id):
                            logging.info(f"New item found for search {search.id}: {item_id}")
                            new_items.append(item)
                    next_page = response_json.get('meta', {}).get('next_page')
                else:
                    next_page = None

        if new_items:
            search_title = query_params.get('keywords', ['no keywords'])[0]
            items_to_notify = []
            for item in new_items:
                item_id = item.get("id")
                # Double-check existence in case of race conditions with concurrent runs
                if not db_helper.search_result_exists(search.id, item_id):
                    logging.info(f"Processing new item {item_id} for search {search.id}")
                    
                    if _item_matches_filters(item, search):
                        logging.info(f"Item {item_id} matches filters. Marking as notified.")
                        db_helper.add_search_result(search.id, item_id, json.dumps(item), notified=True)
                        items_to_notify.append(item)
                    else:
                        logging.info(f"Item {item_id} does not match filters. Marking as not notified.")
                        db_helper.add_search_result(search.id, item_id, json.dumps(item), notified=False)
                else:
                    logging.info(f"Item {item_id} already processed for search {search.id}. Skipping.")

            if items_to_notify:
                logging.info(f"Sending notification for {len(items_to_notify)} items for search {search.id}")
                await format_and_send_message(TELEGRAM_CHAT_ID, search_title, items_to_notify, search)
            else:
                logging.info(f"No new items matching filters to notify for search {search.id}")
        else:
            logging.info(f"No new items found for search {search.id}")
    except Exception as e:
        logging.error(f"Error processing search {search.id}: {e}", exc_info=True)

async def _run_single_search_loop(search, wallapop_client: WallapopClient):
    """The main loop for a single saved search, respecting its period."""
    db_helper = DBHelper()
    while True:
        try:
            await _execute_search(search, wallapop_client, db_helper)
            
            # Convert period from minutes to seconds for sleeping
            sleep_seconds = search.period * 60
            logging.info(f"Search {search.id} finished. Sleeping for {search.period} minutes.")
            await asyncio.sleep(sleep_seconds)
        except asyncio.CancelledError:
            logging.info(f"Search task for search {search.id} was cancelled.")
            break # Exit the loop if the task is cancelled
        except Exception as e:
            logging.error(f"Unhandled error in search loop for {search.id}: {e}. Retrying in 5 minutes.")
            await asyncio.sleep(300) # Wait before retrying on failure
    del db_helper

async def check_saved_searches():
    """Starts and manages monitoring tasks for all saved searches."""
    logging.info("Starting saved searches monitor...")
    wallapop_client = WallapopClient()
    db_helper = DBHelper()

    while True:
        try:
            logging.info("Syncing search tasks with database...")
            current_searches = db_helper.get_all_saved_searches()
            current_search_ids = {s.id for s in current_searches}
            running_search_ids = set(running_tasks.keys())

            # Stop tasks for deleted or modified searches
            for search_id in running_search_ids - current_search_ids:
                logging.info(f"Stopping monitor for deleted search {search_id}")
                running_tasks[search_id].cancel()
                del running_tasks[search_id]

            # Start tasks for new searches
            for search in current_searches:
                if search.id not in running_tasks:
                    logging.info(f"Starting new monitor for search {search.id}")
                    task = asyncio.create_task(_run_single_search_loop(search, wallapop_client))
                    running_tasks[search.id] = task

            # Check for updated searches (e.g., period changed)
            # A simple approach is to restart the task.
            for search in current_searches:
                # This part is for handling updates to existing searches.
                # For simplicity, we can assume for now that updates require a restart of the bot.
                # A more advanced implementation would compare search objects and restart tasks.
                pass

            # This main loop will check for new/deleted searches every 60 seconds.
            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Error in main search monitor loop: {e}", exc_info=True)
            await asyncio.sleep(60) # Wait before retrying

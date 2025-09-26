import logging
import time
import json
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.wallapop.api_client import WallapopClient
from src.wallbot.telegram.notifications import notify_search_results, notify_search_attempt
from src.wallbot.config.settings import TELEGRAM_CHAT_ID

# In-memory store for last run timestamps
last_run_timestamps = {}

def check_saved_searches():
    logging.info("Starting saved searches monitor...")
    db_helper = DBHelper()
    db_helper.setup()
    wallapop_client = WallapopClient()

    while True:
        logging.info("Checking saved searches...")
        saved_searches = db_helper.get_all_saved_searches()

        for search in saved_searches:
            current_time = time.time()
            last_run = last_run_timestamps.get(search.id, 0)

            # Check if it's time to run the search based on its period
            if current_time - last_run > search.period * 60:
                logging.info(f"Trying search {search.id}")
                notify_search_attempt(TELEGRAM_CHAT_ID, search.url)
                new_items_found = False
                try:
                    from urllib.parse import urlparse, parse_qs
                    parsed_url = urlparse(search.url)
                    query_params = parse_qs(parsed_url.query)
                    search_params_filtered = {k: v[0] for k, v in query_params.items()}

                    response_json = wallapop_client.search_items_from_web(**search_params_filtered)
                    logging.info(f"Result status: {response_json is not None}")

                    page_count = 1
                    if response_json:
                        search_objects = response_json.get("search_objects", [])
                        for item in search_objects:
                            item_id = item.get("id")
                            if item_id and not db_helper.search_result_exists(search.id, item_id):
                                db_helper.add_search_result(search.id, item_id, json.dumps(item))
                                logging.info(f"New item found for search {search.id}: {item_id}")
                                new_items_found = True

                        next_page = response_json.get('meta', {}).get('next_page')
                        while next_page and page_count < search.pages:
                            page_count += 1
                            logging.info(f"Getting page number {page_count}")
                            response_json = wallapop_client.search_items_from_web(next_page=next_page)
                            logging.info(f"Result status: {response_json is not None}")
                            if response_json:
                                search_objects = response_json.get("search_objects", [])
                                for item in search_objects:
                                    item_id = item.get("id")
                                    if item_id and not db_helper.search_result_exists(search.id, item_id):
                                        db_helper.add_search_result(search.id, item_id, json.dumps(item))
                                        logging.info(f"New item found for search {search.id}: {item_id}")
                                        new_items_found = True
                                next_page = response_json.get('meta', {}).get('next_page')
                            else:
                                next_page = None

                    if new_items_found:
                        notify_search_results(TELEGRAM_CHAT_ID, search.url)

                except Exception as e:
                    logging.error(f"Error processing search {search.id}: {e}")
                
                last_run_timestamps[search.id] = current_time

        # Wait for 5 minutes before the next check
        time.sleep(300)

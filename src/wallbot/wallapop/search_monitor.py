import logging
import time
import json
import asyncio
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.wallapop.api_client import WallapopClient
from src.wallbot.telegram.notifications import notify_grouped_search_results
from src.wallbot.config.settings import TELEGRAM_CHAT_ID

# In-memory store for last run timestamps
last_run_timestamps = {}

async def check_saved_searches():
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

            if current_time - last_run > search.period * 60:
                logging.info(f"Trying search {search.id}")
                new_items = []
                try:
                    from urllib.parse import urlparse, parse_qs
                    parsed_url = urlparse(search.url)
                    query_params = parse_qs(parsed_url.query)
                    search_params_filtered = {k: v[0] for k, v in query_params.items()}

                    response_json = wallapop_client.search_items_from_web(**search_params_filtered)
                    logging.info(f"Result status: {response_json is not None}")

                    page_count = 1
                    if response_json:
                        raw_items = response_json.get('data', {}).get('section', {}).get('payload', {}).get('items', [])
                        for item in raw_items:
                            item_id = item.get("id")
                            if item_id and not db_helper.search_result_exists(search.id, item_id):
                                db_helper.add_search_result(search.id, item_id, json.dumps(item))
                                logging.info(f"New item found for search {search.id}: {item_id}")
                                new_items.append(item)

                        next_page = response_json.get('meta', {}).get('next_page')
                        while next_page and page_count < search.pages:
                            page_count += 1
                            logging.info(f"Getting page number {page_count}")
                            response_json = wallapop_client.search_items_from_web(next_page=next_page)
                            logging.info(f"Result status: {response_json is not None}")
                            if response_json:
                                raw_items = response_json.get('data', {}).get('section', {}).get('payload', {}).get('items', [])
                                for item in raw_items:
                                    item_id = item.get("id")
                                    if item_id and not db_helper.search_result_exists(search.id, item_id):
                                        db_helper.add_search_result(search.id, item_id, json.dumps(item))
                                        logging.info(f"New item found for search {search.id}: {item_id}")
                                        new_items.append(item)
                                next_page = response_json.get('meta', {}).get('next_page')
                            else:
                                next_page = None

                    if new_items:
                        search_title = query_params.get('keywords', ['no keywords'])[0]
                        message = f"Search: {search_title}\n"
                        for i, item in enumerate(new_items, 1):
                            item_title = item.get('title', 'No title')
                            item_price = item.get('price', {'amount': 'N/A'}).get('amount', 'N/A')
                            item_url = item.get('web_slug', 'No link')
                            message += f"{i}- {item_title} - {item_price}\n    https://es.wallapop.com/item/{item_url}\n"
                        await notify_grouped_search_results(TELEGRAM_CHAT_ID, message)

                except Exception as e:
                    logging.error(f"Error processing search {search.id}: {e}")
                
                last_run_timestamps[search.id] = current_time

        await asyncio.sleep(300)

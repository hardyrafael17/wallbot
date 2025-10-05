import locale
import logging
import queue
import threading
import time
import asyncio
from telegram import Bot
from telegram.helpers import escape_markdown
from src.wallbot.config.constants import ICON_EXCLAMATION, ICON_DIRECT_HIT, ICON_COLLISION
from src.wallbot.config.settings import TOKEN, TELEGRAM_CHAT_ID

bot = Bot(TOKEN)
message_queue = queue.Queue()

def _message_sender_worker():
    """
    A worker that runs in a separate thread to send messages from a queue,
    respecting a delay between messages to avoid rate limiting.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def send_async(chat_id, text, parse_mode):
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            logging.info(f"Sent message to chat_id: {chat_id}")
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")

    while True:
        chat_id, text, parse_mode = message_queue.get()
        logging.debug(f"Retrieved message from queue for chat_id: {chat_id}")
        logging.debug(f"Attempting to send message to chat_id: {chat_id}")
        loop.run_until_complete(send_async(chat_id, text, parse_mode))
        time.sleep(3) # Wait for 3 seconds before sending the next message
        logging.debug("Worker finished sending and is now sleeping for 3 seconds.")

async def send_telegram_message(chat_id, text, parse_mode=None):
    try:
        # Instead of sending directly, put the message in the queue
        logging.debug(f"Adding message to queue for chat_id: {chat_id}")
        message_queue.put((chat_id, text, parse_mode))
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

async def format_and_send_message(chat_id, search_title, new_items, search):
    if not new_items:
        return # No items to notify after filtering

    search_title = escape_markdown(search_title, version=2)
    header = f"**Busqueda:** {search_title}\n"
    await notify_grouped_search_results(chat_id, header, new_items)

async def notify_grouped_search_results(chat_id, header, items):
    """
    Sends new items as a grouped message, splitting them into multiple messages
    if the total length exceeds Telegram's limit, ensuring that no item's
    message is broken in the middle.
    """
    max_length = 4096
    message_part = header

    for i, item in enumerate(items, 1):
        item_title = escape_markdown(item.get('title', 'No title'), version=2)
        item_price = escape_markdown(str(item.get('price', {}).get('amount', 'N/A')), version=2)
        item_url = item.get('web_slug', 'No link')
        item_line = f"{i}\\. [{item_title}](https://es.wallapop.com/item/{item_url}) \\- **Precio:** {item_price}\n"

        if len(message_part) + len(item_line) > max_length:
            await send_telegram_message(chat_id, message_part, parse_mode='MarkdownV2')
            message_part = header # Start a new message with the header
        
        message_part += item_line

    if message_part != header: # Send the last part if it has items
        await send_telegram_message(chat_id, message_part, parse_mode='MarkdownV2')

# Start the sender worker thread
sender_thread = threading.Thread(target=_message_sender_worker, daemon=True)
sender_thread.start()

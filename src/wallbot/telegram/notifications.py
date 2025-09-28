import locale
import logging
from telegram import Bot
from telegram.helpers import escape_markdown
from src.wallbot.config.constants import ICON_EXCLAMATION, ICON_DIRECT_HIT, ICON_COLLISION
from src.wallbot.config.settings import TOKEN, TELEGRAM_CHAT_ID

bot = Bot(TOKEN)

async def send_telegram_message(chat_id, text, parse_mode=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

async def format_and_send_message(chat_id, search_title, new_items):
    search_title = escape_markdown(search_title, version=2)
    message = f"**Busqueda:** {search_title}\n"
    for i, item in enumerate(new_items, 1):
        item_title = escape_markdown(item.get('title', 'No title'), version=2)
        item_price = escape_markdown(str(item.get('price', {'amount': 'N/A'}).get('amount', 'N/A')), version=2)
        item_url = item.get('web_slug', 'No link')
        message += f"{i}\\. [{item_title}](https://es.wallapop.com/item/{item_url}) \\- **Precio:** {item_price}\n"
    
    await notify_grouped_search_results(chat_id, message)

async def notify_grouped_search_results(chat_id, message):
    max_length = 4096
    if len(message) <= max_length:
        await send_telegram_message(chat_id, message, parse_mode='MarkdownV2')
        return

    lines = message.split('\n')
    part = ""
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            line1 = lines[i]
            line2 = lines[i+1]
            
            if len(part) + len(line1) + len(line2) + 2 > max_length:
                await send_telegram_message(chat_id, part, parse_mode='MarkdownV2')
                part = ""

            if part:
                part += "\n"
            part += f"{line1}\n{line2}"
        else:
            if len(part) + len(lines[i]) + 1 > max_length:
                await send_telegram_message(chat_id, part, parse_mode='MarkdownV2')
                part = ""
            
            if part:
                part += "\n"
            part += lines[i]

    if part:
        await send_telegram_message(chat_id, part, parse_mode='MarkdownV2')

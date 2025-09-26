import locale
import logging
from telegram import Bot
from src.wallbot.config.constants import ICON_EXCLAMATION, ICON_DIRECT_HIT, ICON_COLLISION
from src.wallbot.config.settings import TOKEN, TELEGRAM_CHAT_ID

bot = Bot(TOKEN)

async def send_telegram_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

async def notel(chat_id, price, title, url_item, obs=None):
    # https://apps.timwhitlock.info/emoji/tables/unicode
    if obs is not None:
        text = ICON_EXCLAMATION
    else:
        text = ICON_DIRECT_HIT
    text += f' *{title}*'
    text += '\n'
    if obs is not None:
        text += f'{ICON_COLLISION} '
    text += locale.currency(price, grouping=True)
    if obs is not None:
        text += obs
        text += f' {ICON_COLLISION}'
    text += '\n'
    text += f'https://es.wallapop.com/item/{url_item}'
    await send_telegram_message(chat_id, text)

async def notify_grouped_search_results(chat_id, message):
    max_length = 4000
    if len(message) > max_length:
        for i in range(0, len(message), max_length):
            await send_telegram_message(chat_id, message[i:i+max_length])
    else:
        await send_telegram_message(chat_id, message)

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

async def notel(chat_id, price, title, url_item, obs=None):
    # https://apps.timwhitlock.info/emoji/tables/unicode
    if obs is not None:
        icon = ICON_EXCLAMATION
    else:
        icon = ICON_DIRECT_HIT
    
    title = escape_markdown(title, version=2)
    price_str = escape_markdown(locale.currency(price, grouping=True), version=2)

    text = f"{icon} *{title}*\n"
    if obs is not None:
        text += f"{ICON_COLLISION} "
    text += f"`{price_str}`"
    if obs is not None:
        obs_text = escape_markdown(obs, version=2)
        text += f" {obs_text} {ICON_COLLISION}"
    
    text += f"\n[View on Wallapop](https://es.wallapop.com/item/{url_item})"
    
    await send_telegram_message(chat_id, text, parse_mode='MarkdownV2')

async def notify_grouped_search_results(chat_id, message):
    max_length = 4096
    if len(message) <= max_length:
        await send_telegram_message(chat_id, message)
        return

    lines = message.split('\n')
    part = ""
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            line1 = lines[i]
            line2 = lines[i+1]
            
            if len(part) + len(line1) + len(line2) + 2 > max_length:
                await send_telegram_message(chat_id, part)
                part = ""

            if part:
                part += "\n"
            part += f"{line1}\n{line2}"
        else:
            if len(part) + len(lines[i]) + 1 > max_length:
                await send_telegram_message(chat_id, part)
                part = ""
            
            if part:
                part += "\n"
            part += lines[i]

    if part:
        await send_telegram_message(chat_id, part)

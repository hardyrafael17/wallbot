import locale
import logging
import requests

from src.wallbot.config.constants import ICON_EXCLAMATION, ICON_DIRECT_HIT, ICON_COLLISION
from src.wallbot.config.settings import TELEGRAM_API_URL


def send_telegram_message(chat_id, text):
    url = TELEGRAM_API_URL + f"sendMessage?chat_id={chat_id}&text={text}"
    try:
        response = requests.get(url)
        logging.info(f"Telegram API response: {response.status_code} - {response.text}")
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram message: {e}")


def notel(chat_id, price, title, url_item, obs=None):
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
    send_telegram_message(chat_id, text)


def notify_search_results(chat_id, search_url):
    text = f"results found for search -{search_url}-"
    send_telegram_message(chat_id, text)

def notify_search_attempt(chat_id, search_url):
    text = f"searching saved search {search_url}"
    send_telegram_message(chat_id, text)

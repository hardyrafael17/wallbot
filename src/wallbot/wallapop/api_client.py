import logging

import requests

from src.wallbot.config.settings import WALLAPOP_API_URL
from src.wallbot.database.models import ChatSearch


class WallapopClient:
    def __init__(self):
        self.base_url = WALLAPOP_API_URL
        self.headers = {'x-deviceos': '0'}

    def search_items(self, search: ChatSearch):
        url = self._build_search_url(search)
        logging.debug(f"API Wallapop ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            logging.debug(f"API Wallapop <-: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop: {e}")
            return None

    def _build_search_url(self, search):
        url = f"{self.base_url}?source=search_box"
        url += f"&keywords={'+'.join(search.kws.split(' '))}"
        url += "&time_filter=today"

        if search.cat_ids:
            url += f"&category_ids={search.cat_ids}"
        if search.min_price:
            url += f"&min_sale_price={search.min_price}"
        if search.max_price:
            url += f"&max_sale_price={search.max_price}"
        if search.dist:
            url += f"&dist={search.dist}"
        if search.orde:
            url += f"&order_by={search.orde}"

        return url

    def search_items_from_web(self, **kwargs):
        url = f"{self.base_url}?source=search_box"
        if 'keywords' in kwargs and kwargs['keywords']:
            url += f"&keywords={'+'.join(kwargs['keywords'].split(' '))}"
        if 'category_ids' in kwargs and kwargs['category_ids']:
            url += f"&category_ids={kwargs['category_ids']}"
        if 'min_price' in kwargs and kwargs['min_price']:
            url += f"&min_sale_price={kwargs['min_price']}"
        if 'max_price' in kwargs and kwargs['max_price']:
            url += f"&max_sale_price={kwargs['max_price']}"
        if 'distance' in kwargs and kwargs['distance']:
            url += f"&dist={kwargs['distance']}"
        if 'order_by' in kwargs and kwargs['order_by']:
            url += f"&order_by={kwargs['order_by']}"
        if 'latitude' in kwargs and kwargs['latitude']:
            url += f"&latitude={kwargs['latitude']}"
        if 'longitude' in kwargs and kwargs['longitude']:
            url += f"&longitude={kwargs['longitude']}"

        logging.debug(f"API Wallapop (Web) ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            logging.debug(f"API Wallapop (Web) <-: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop (Web): {e}")
            return None

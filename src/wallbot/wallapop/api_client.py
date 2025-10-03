import logging

import requests

from src.wallbot.config.settings import WALLAPOP_API_URL, WALLAPOP_ITEM_URL, WALLAPOP_USER_URL
from src.wallbot.database.models import ChatSearch


class WallapopClient:
    def __init__(self):
        self.base_url = WALLAPOP_API_URL
        self.item_url = WALLAPOP_ITEM_URL
        self.user_url = WALLAPOP_USER_URL
        self.headers = {
            'x-deviceos': '0',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0'
        }

    def make_request(self, method, url, data=None, json=None, headers=None):
        """Makes a request to a given URL with the specified method and returns the response object."""
        logging.debug(f"Making {method} request to URL: {url}")
        
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
            
        try:
            response = requests.request(method, url, headers=request_headers, data=data, json=json, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"Error in API Wallapop ({method}) for URL {url}: {e}")
            if e.response is not None:
                # Return the response even if it's an error, so the caller can inspect it
                return e.response
            return None

    def search_items(self, search: ChatSearch):
        url = self._build_search_url(search)
        # logging.debug(f"API Wallapop ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            # logging.debug(f" API Wallapop <-: {response.json()}")
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
        import uuid
        
        if 'next_page' in kwargs and kwargs['next_page']:
            url = f"{self.base_url}?next_page={kwargs['next_page']}"
        else:
            url = f"{self.base_url}?source=search_box&search_id={uuid.uuid4()}"
            if 'keywords' in kwargs and kwargs['keywords']:
                url += f"&keywords={'+'.join(kwargs['keywords'].split(' '))}"
            if 'category_id' in kwargs and kwargs['category_id']:
                url += f"&category_id={kwargs['category_id']}"
            if 'subcategory_ids' in kwargs and kwargs['subcategory_ids']:
                url += f"&subcategory_ids={kwargs['subcategory_ids']}"
            if 'min_price' in kwargs and kwargs['min_price']:
                url += f"&min_sale_price={kwargs['min_price']}"
            if 'max_price' in kwargs and kwargs['max_price']:
                url += f"&max_sale_price={kwargs['max_price']}"
            if 'distance_in_km' in kwargs and kwargs['distance_in_km']:
                url += f"&distance_in_km={kwargs['distance_in_km']}"
            if 'latitude' in kwargs and kwargs['latitude']:
                url += f"&latitude={kwargs['latitude']}"
            if 'longitude' in kwargs and kwargs['longitude']:
                url += f"&longitude={kwargs['longitude']}"
            if 'time_filter' in kwargs and kwargs['time_filter']:
                url += f"&time_filter={kwargs['time_filter']}"
            if 'order_by' in kwargs and kwargs['order_by']:
                url += f"&order_by={kwargs['order_by']}"

        # logging.info(f"API Wallapop (Web) ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop (Web): {e}")
            return None
        except requests.exceptions.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from Wallapop (Web): {e}")
            return None

    def get_item_details(self, item_id: str):
        url = self.item_url.format(item_id=item_id)
        logging.debug(f"API Wallapop (Item) ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            logging.debug(f"API Wallapop (Item) <-: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop (Item): {e}")
            return None

    def get_user_by_id(self, user_id: str):
        url = self.user_url.format(user_id=user_id)
        logging.debug(f"API Wallapop (User) ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            logging.debug(f"API Wallapop (User) <-: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop (User): {e}")
            return None

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        logging.debug(f"API Wallapop (GET) ->: {url} with params {params}")
        try:
            response = requests.get(url=url, headers=self.headers, params=params)
            # Log the response for debugging
            # logging.debug(f"API Wallapop (GET) <-: {response.status_code} {response.text}")
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop (GET): {e}")
            return None
import logging
import json
import sqlite3
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from src.wallbot.wallapop.api_client import WallapopClient
from src.wallbot.wallapop.api_models import ApiSearchItem, ApiPrice, ApiImage, ApiImageUrls, ApiLocation, ApiShipping, ApiTaxonomy, ApiDiscount
from src.wallbot.wallapop.categories import CategoryService
from src.wallbot.database.models import Item


def _parse_search_args(args):
    """
    Parses search arguments from a list of strings into keywords and parameters.
    Example: ['ps5', 'digital', 'min_p=300', 'max_p=400']
    """
    kws_list = []
    params = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Map web param names to database column names if they differ
            param_map = {
                'min_p': 'min_price',
                'max_p': 'max_price',
                'cat': 'cat_ids',
                'dist': 'dist',
                'order': 'orde'
            }
            db_key = param_map.get(key, key)
            params[db_key] = value
        else:
            kws_list.append(arg)

    kws = ' '.join(kws_list)
    return kws, params


def _parse_api_item(item_json):
    """Parses a JSON item from Wallapop API into an ApiSearchItem object."""
    try:
        # Helper to safely get nested dictionary values
        def get_flag(key):
            return item_json.get(key, {}).get('flag', 0) == 1

        images = [
            ApiImage(
                id=img['id'],
                urls=ApiImageUrls(**img['urls']),
                average_color=img['average_color']
            ) for img in item_json.get('images', [])
        ]
        
        location_data = item_json.get('location', {})
        location = ApiLocation(
            latitude=location_data.get('latitude'),
            longitude=location_data.get('longitude'),
            postal_code=location_data.get('postal_code'),
            city=location_data.get('city'),
            country_code=location_data.get('country_code'),
            region=location_data.get('region'),
            region2=location_data.get('region2')
        )

        shipping_data = item_json.get('shipping', {})
        shipping = ApiShipping(
            item_is_shippable=shipping_data.get('item_is_shippable', False),
            user_allows_shipping=shipping_data.get('user_allows_shipping', False),
            cost_configuration_id=shipping_data.get('cost_configuration_id')
        )

        taxonomy = [ApiTaxonomy(**tax) for tax in item_json.get('taxonomy', [])]
        
        discount_data = item_json.get('discount')
        discount = None
        if discount_data:
            discount = ApiDiscount(
                percentage=discount_data['percentage'],
                previous_price=ApiPrice(**discount_data['previous_price'])
            )

        return ApiSearchItem(
            id=item_json['id'],
            title=item_json['title'],
            description=item_json['description'],
            price=ApiPrice(**item_json['price']),
            category_id=item_json['category_id'],
            user_id=item_json['user_id'],
            created_at=item_json['created_at'],
            modified_at=item_json['modified_at'],
            web_slug=item_json['web_slug'],
            images=images,
            location=location,
            shipping=shipping,
            taxonomy=taxonomy,
            is_refurbished=get_flag('is_refurbished'),
            is_favoriteable=get_flag('is_favoriteable'),
            is_top_profile=get_flag('is_top_profile'),
            has_warranty=get_flag('has_warranty'),
            reserved=get_flag('reserved'),
            favorited=get_flag('favorited'),
            bump=item_json.get('bump', {}),
            discount=discount
        )
    except (KeyError, TypeError) as e:
        logging.error(f"Error parsing API item: {e} - Item: {item_json}")
        return None


def create_web_app(db):
    """
    Creates and configures the Flask web application.
    Args:
        db: An instance of DBHelper to interact with the database.
    """
    app = Flask(__name__)

    def fromjson_filter(value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def attr_filter(value, key, index=None):
        try:
            res = value[key]
            if index is not None:
                return res[index]
            return res
        except (KeyError, IndexError, TypeError):
            return None

    app.jinja_env.filters['fromjson'] = fromjson_filter
    app.jinja_env.filters['attr'] = attr_filter

    # A secret key is required for flashing messages
    app.secret_key = 'supersecretkey'
    wallapop_client = WallapopClient()
    
    category_service = CategoryService(wallapop_client)
    category_service.load_categories()

    @app.route('/')
    def index():
        return redirect(url_for('manual_search'))

    @app.route('/searches')
    def manage_searches():
        """Displays all saved searches."""
        try:
            all_searches = db.get_chats_searches()
            return render_template('searches.html', searches=all_searches)
        except Exception as e:
            logging.error(f"Error fetching searches for web UI: {e}")
            flash("Error loading searches from the database.", "error")
            return render_template('searches.html', searches=[])

    @app.route('/searches/add', methods=['POST'])
    def add_search():
        """Adds a new search from the form input."""
        search_input = request.form.get('search_input', '').strip()
        if not search_input:
            flash("Input cannot be empty.", "error")
            return redirect(url_for('manage_searches'))

        parts = search_input.split()
        if len(parts) < 2:
            flash("Invalid format. Use: <chat_id> <keyword(s)> [param=value...]", "error")
            return redirect(url_for('manage_searches'))

        chat_id, args = parts[0], parts[1:]
        kws, params = _parse_search_args(args)

        try:
            db.add_search(chat_id, kws, **params)
            flash(f"Successfully added search for chat ID {chat_id}.", "success")
        except Exception as e:
            logging.error(f"Error adding search via web UI: {e}")
            flash(f"Error adding search: {e}", "error")

        return redirect(url_for('manage_searches'))

    @app.route('/searches/delete/<int:search_id>', methods=['POST'])
    def delete_search(search_id):
        """Deletes a search."""
        db.remove_search(search_id)
        flash(f"Search #{search_id} has been deleted.", "success")
        return redirect(url_for('manage_searches'))

    @app.route('/saved_searches')
    def saved_searches():
        """Displays all saved searches."""
        try:
            all_searches = db.get_all_saved_searches()
            return render_template('saved_searches.html', searches=all_searches)
        except Exception as e:
            logging.error(f"Error fetching saved searches for web UI: {e}")
            flash("Error loading saved searches from the database.", "error")
            return render_template('saved_searches.html', searches=[])

    @app.route('/api/saved_searches', methods=['POST'])
    def add_saved_search():
        """Adds a new saved search."""
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'success': False, 'error': 'URL is required.'}), 400
        try:
            db.add_saved_search(url)
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'error': 'URL already saved.'}), 409
        except Exception as e:
            logging.error(f"Error adding saved search: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/saved_searches/delete/<int:search_id>', methods=['POST'])
    def delete_saved_search(search_id):
        """Deletes a saved search."""
        try:
            db.delete_saved_search(search_id)
            flash(f"Saved search #{search_id} has been deleted.", "success")
        except Exception as e:
            logging.error(f"Error deleting saved search: {e}")
            flash("Error deleting saved search.", "error")
        return redirect(url_for('saved_searches'))

    @app.route('/api/saved_searches/update/<int:search_id>', methods=['POST'])
    def update_saved_search(search_id):
        """Updates a saved search."""
        url = request.form.get('url')
        period = request.form.get('period')
        pages = request.form.get('pages')
        try:
            db.update_saved_search(search_id, url, period, pages)
            flash(f"Saved search #{search_id} has been updated.", "success")
        except Exception as e:
            logging.error(f"Error updating saved search: {e}")
            flash("Error updating saved search.", "error")
        return redirect(url_for('saved_searches'))

    @app.route('/api/saved_items', methods=['POST'])
    def add_saved_item():
        """Adds a new saved item."""
        item_data = request.get_json()
        if not item_data or 'id' not in item_data:
            return jsonify({'success': False, 'error': 'Invalid item data.'}), 400
        
        try:
            # Create an Item object from the received data
            item = Item(
                item_id=item_data.get('id'),
                chat_id=None, # chat_id is not relevant for saved items from web UI
                title=item_data.get('title'),
                price=item_data.get('price', {}).get('amount'),
                url=f"https://wallapop.com/item/{item_data.get('web_slug')}",
                publish_date=None, # Not directly available in this context
                description=item_data.get('description'),
                item=json.dumps(item_data), # Store the full item JSON
                notes=None # Initialize notes as None
            )
            db.add_saved_item(item)
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'error': 'Item already saved.'}), 409
        except Exception as e:
            logging.error(f"Error adding saved item: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/saved_items_list')
    def saved_items_list():
        """Displays all saved items."""
        try:
            all_saved_items = db.get_all_saved_items()
            return render_template('saved_items_list.html', saved_items=all_saved_items)
        except Exception as e:
            logging.error(f"Error fetching saved items for web UI: {e}")
            flash("Error loading saved items from the database.", "error")
            return render_template('saved_items_list.html', saved_items=[])

    @app.route('/api/saved_items/<item_id>', methods=['DELETE'])
    def delete_saved_item_api(item_id):
        """Deletes a saved item."""
        try:
            db.delete_saved_item(item_id)
            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"Error deleting saved item {item_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/saved_items/<item_id>/notes', methods=['POST'])
    def update_saved_item_notes_api(item_id):
        """Updates notes for a saved item."""
        data = request.get_json()
        notes = data.get('notes')
        try:
            db.update_saved_item_notes(item_id, notes)
            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"Error updating notes for saved item {item_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/manual-search', methods=['GET', 'POST'])
    def manual_search():
        results = []
        all_raw_items = []
        search_params = {}
        if request.method == 'POST':
            all_raw_items = []
            request_url = request.form.get('request_url')
            if request_url:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(request_url)
                query_params = parse_qs(parsed_url.query)
                # Convert lists of values from parse_qs to single values
                search_params_filtered = {k: v[0] for k, v in query_params.items()}
                response_json = wallapop_client.search_items_from_web(**search_params_filtered)
                search_params = search_params_filtered
            else:
                search_params = {
                    'keywords': request.form.get('keywords'),
                    'min_price': request.form.get('min_price'),
                    'max_price': request.form.get('max_price'),
                    'category_id': request.form.get('category_id'),
                    'subcategory_ids': request.form.get('subcategory_ids'),
                    'time_filter': request.form.get('time_filter'),
                    'order_by': request.form.get('order_by'),
                }

                latitude = request.form.get('latitude')
                longitude = request.form.get('longitude')

                if latitude and longitude:
                    search_params['latitude'] = latitude
                    search_params['longitude'] = longitude
                    search_params['distance_in_km'] = request.form.get('distance_in_km')

                # Filter out empty params
                search_params_filtered = {k: v for k, v in search_params.items() if v}
                response_json = wallapop_client.search_items_from_web(**search_params_filtered)

            fetch_all = request.form.get('fetch_all') == 'on'
            num_pages = int(request.form.get('num_pages', 1))
            max_pages = 20
            
            if response_json and 'data' in response_json:
                raw_items = response_json.get('data', {}).get('section', {}).get('payload', {}).get('items', [])
                all_raw_items.extend(raw_items)
                results.extend([item for item in [_parse_api_item(item) for item in raw_items] if item])
                
                next_page = response_json.get('meta', {}).get('next_page')
                
                page_count = 1
                items_on_prev_page = len(raw_items)
                while next_page and page_count < max_pages and (fetch_all or page_count < num_pages):
                    page_count += 1
                    logging.info(f"Fetching page {page_count}, items on previous page: {items_on_prev_page}")
                    response_json = wallapop_client.search_items_from_web(next_page=next_page)
                    if response_json and 'data' in response_json:
                        raw_items = response_json.get('data', {}).get('section', {}).get('payload', {}).get('items', [])
                        all_raw_items.extend(raw_items)
                        items_on_prev_page = len(raw_items)
                        results.extend([item for item in [_parse_api_item(item) for item in raw_items] if item])
                        next_page = response_json.get('meta', {}).get('next_page')
                    else:
                        next_page = None
                        items_on_prev_page = 0

                if not results:
                    flash("No results found for your search.", "info")

        return render_template('manual_search.html', results=results, raw_results=all_raw_items, search_params=search_params)

    @app.route('/get-item-details/<item_id>')
    def get_item_details(item_id):
        item_details = wallapop_client.get_item_details(item_id)
        if not item_details:
            return jsonify({'error': 'Item not found'}), 404

        user_id = item_details.get('user', {}).get('id')
        if user_id:
            user_details = wallapop_client.get_user_by_id(user_id)
            item_details['user_details'] = user_details

        return jsonify(item_details)

    @app.route('/api/categories')
    def get_categories():
        return jsonify(json.loads(category_service.get_categories_as_json()))

    @app.route('/restart', methods=['POST'])
    def restart():
        logging.info("Restarting application...")
        os.execv(sys.executable, [sys.executable, '-m', 'src.wallbot'])

    return app

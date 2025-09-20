import logging
from flask import Flask, render_template, request, redirect, url_for, flash

from src.wallbot.wallapop.api_client import WallapopClient
from src.wallbot.wallapop.api_models import ApiSearchItem, ApiPrice, ApiImage, ApiImageUrls, ApiLocation, ApiShipping, ApiTaxonomy, ApiDiscount


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
    # A secret key is required for flashing messages
    app.secret_key = 'supersecretkey'
    wallapop_client = WallapopClient()

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

    @app.route('/manual-search', methods=['GET', 'POST'])
    def manual_search():
        results = []
        if request.method == 'POST':
            search_params = {
                'keywords': request.form.get('keywords'),
                'min_price': request.form.get('min_price'),
                'max_price': request.form.get('max_price'),
                'category_ids': request.form.get('category_ids'),
                'order_by': request.form.get('order_by'),
                'latitude': request.form.get('latitude'),
                'longitude': request.form.get('longitude'),
                'distance': request.form.get('distance'),
            }
            # Filter out empty params
            search_params = {k: v for k, v in search_params.items() if v}
            
            response_json = wallapop_client.search_items_from_web(**search_params)
            
            if response_json and 'data' in response_json:
                raw_items = response_json['data'].get('section', {}).get('payload', {}).get('items', [])
                results = [_parse_api_item(item) for item in raw_items]
                results = [item for item in results if item] # Filter out parsing errors
                if not results:
                    flash("No results found for your search.", "info")

        return render_template('manual_search.html', results=results)

    return app

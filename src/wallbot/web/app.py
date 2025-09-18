import logging
from flask import Flask, render_template, request, redirect, url_for, flash


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


def create_web_app(db):
    """
    Creates and configures the Flask web application.
    Args:
        db: An instance of DBHelper to interact with the database.
    """
    app = Flask(__name__)
    # A secret key is required for flashing messages
    app.secret_key = 'supersecretkey'

    @app.route('/')
    def index():
        return redirect(url_for('manage_searches'))

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

    return app
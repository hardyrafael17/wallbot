from flask import Flask, render_template, jsonify
from ..database.db_helper import DBHelper

app = Flask(__name__, template_folder='templates')
db = DBHelper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/searches')
def get_searches():
    searches = db.get_chats_searches()
    search_list = []
    for search in searches:
        search_list.append({
            'chat_id': search.chat_id,
            'kws': search.kws,
            'cat_ids': search.cat_ids,
            'min_price': search.min_price,
            'max_price': search.max_price,
            'dist': search.dist,
            'publish_date': search.publish_date,
            'orde': search.orde,
            'username': search.username,
            'name': search.name,
            'active': search.active
        })
    return jsonify(search_list)

if __name__ == '__main__':
    app.run(debug=True)

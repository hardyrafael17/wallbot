import logging
import sqlite3
import time
from typing import List

from src.wallbot.config.settings import DATABASE_PATH
from src.wallbot.database.models import ChatSearch, Item, SavedSearch


class DBHelper:
    def __init__(self, dbname=None):
        # Use the centralized DATABASE_PATH from settings, but allow overrides.
        calculated_db_name = dbname if dbname is not None else DATABASE_PATH
        # logging.info(f"DB: {calculated_db_name}")
        self.__conn = sqlite3.connect(calculated_db_name, timeout=15, check_same_thread=False)

    def setup(self, version=""):
        tblstmtitem = "create table if not exists item " \
                      "(itemId integer, " \
                      "chatId text, " \
                      "title text, " \
                      "price text, " \
                      "url text, " \
                      "user text, " \
                      "publishDate integer, " \
                      "description text, " \
                      "item text, " \
                      "notes text, " \
                      " primary key (itemId,chatId))"
        self.__conn.execute(tblstmtitem)

        tblstmtchat = "create table if not exists chat_search " \
                      "(chat_id text, " \
                      "kws text, " \
                      "cat_ids text, " \
                      "min_price text, " \
                      "max_price text, " \
                      "dist text default '400', " \
                      "publish_date integer default 24, " \
                      "ord text default 'newest', " \
                      "username text, " \
                      "name text, " \
                      "active int default 1)"
        self.__conn.execute(tblstmtchat)

        tblstmtsavedsearches = "create table if not exists saved_searches " \
                               "(id integer primary key autoincrement, " \
                               "url text not null unique)"
        self.__conn.execute(tblstmtsavedsearches)

        # Each ALTER TABLE should be in its own try/except block
        # to handle columns being added incrementally across versions.
        try:
            self.__conn.execute("alter table saved_searches add column period integer default 5")
        except sqlite3.OperationalError:
            pass # Column already exists
        try:
            self.__conn.execute("alter table saved_searches add column pages integer default 2")
        except sqlite3.OperationalError:
            pass # Column already exists
        try:
            self.__conn.execute("alter table saved_searches add column positive_words text default ''")
        except sqlite3.OperationalError:
            pass # Column already exists
        try:
            self.__conn.execute("alter table saved_searches add column negative_words text default ''")
        except sqlite3.OperationalError:
            pass # Column already exists

        tblstmtsaveditems = "create table if not exists saved_items " \
                              "(item_id text primary key, " \
                              "chat_id text, " \
                              "title text, " \
                              "price text, " \
                              "url text, " \
                              "publish_date integer, " \
                              "description text, " \
                              "item text, " \
                              "notes text)"
        self.__conn.execute(tblstmtsaveditems)

        tblstmtsearchresults = "create table if not exists search_results " \
                                 "(search_id integer, " \
                                 "item_id text, " \
                                 "item_json text, " \
                                 "skipped boolean default false, " \
                                 "primary key (search_id, item_id))"
        self.__conn.execute(tblstmtsearchresults)

        # Add 'skipped' column to 'search_results' if it doesn't exist
        try:
            self.__conn.execute("alter table search_results add column skipped boolean default false")
        except sqlite3.OperationalError:
            pass # Column already exists

        try:
            self.__conn.execute("alter table saved_items add column item_id text")
            self.__conn.execute("update saved_items set item_id = rowid where item_id is null")
            self.__conn.commit()
        except sqlite3.OperationalError:
            pass

        if version == '1.0.6':
            stmt = "update chat_search " \
                   "set ord = 'newest' " \
                   "where ord = 'creationDate-des'"
            try:
                self.__conn.execute(stmt)
                self.__conn.commit()
            except Exception as e:
                logging.error(f"Error setting up the db: {e}")

        self.__conn.commit()

    def add_saved_search(self, url, period=5, pages=2):
        stmt = "insert into saved_searches (url, period, pages) values (?, ?, ?)"
        try:
            self.__conn.execute(stmt, (url, period, pages))
            self.__conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"URL already exists in saved_searches: {url}")
            raise

    def get_all_saved_searches(self) -> List[SavedSearch]:
        stmt = "select id, url, period, pages, positive_words, negative_words from saved_searches order by id desc"
        searches = []
        try:
            for row in self.__conn.execute(stmt):
                searches.append(SavedSearch(id=row[0], url=row[1], period=row[2], pages=row[3], positive_words=row[4], negative_words=row[5]))
        except Exception as e:
            logging.error(f"Error getting all saved searches: {e}")
        return searches

    def get_saved_search_by_id(self, search_id) -> SavedSearch:
        stmt = "select id, url, period, pages, positive_words, negative_words from saved_searches where id = ?"
        try:
            row = self.__conn.execute(stmt, (search_id,)).fetchone()
            if row:
                return SavedSearch(id=row[0], url=row[1], period=row[2], pages=row[3], positive_words=row[4], negative_words=row[5])
        except Exception as e:
            logging.error(f"Error getting saved search by id: {e}")
        return None

    def add_search_result(self, search_id, item_id, item_json, skipped=False):
        stmt = "insert into search_results (search_id, item_id, item_json, skipped) values (?, ?, ?, ?)"
        try:
            self.__conn.execute(stmt, (search_id, item_id, item_json, skipped))
            self.__conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"Item {item_id} already exists for search {search_id}")
            raise

    def search_result_exists(self, search_id, item_id):
        stmt = "select 1 from search_results where search_id = ? and item_id = ?"
        try:
            return self.__conn.execute(stmt, (search_id, item_id)).fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking if search result exists for search {search_id} and item {item_id}: {e}")
            return False

    def delete_saved_search(self, search_id):
        """Deletes a saved search and its associated results."""
        try:
            # Delete associated results first to maintain data integrity
            stmt_results = "delete from search_results where search_id = ?"
            self.__conn.execute(stmt_results, (search_id,))
            stmt = "delete from saved_searches where id = ?"
            self.__conn.execute(stmt, (search_id,))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting saved search with id {search_id}: {e}")

    def update_saved_search(self, search_id, url, period, pages, positive_words, negative_words):
        stmt = "update saved_searches set url = ?, period = ?, pages = ?, positive_words = ?, negative_words = ? where id = ?"
        try:
            self.__conn.execute(stmt, (url, period, pages, positive_words, negative_words, search_id))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error updating saved search with id {search_id}: {e}")

    def update_positive_words(self, search_id, positive_words):
        stmt = "update saved_searches set positive_words = ? where id = ?"
        try:
            self.__conn.execute(stmt, (positive_words, search_id))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error updating positive words for saved search with id {search_id}: {e}")

    def update_negative_words(self, search_id, negative_words):
        stmt = "update saved_searches set negative_words = ? where id = ?"
        try:
            self.__conn.execute(stmt, (negative_words, search_id))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error updating negative words for saved search with id {search_id}: {e}")

    def update_saved_item_notes(self, item_id, notes):
        stmt = "update saved_items set notes = ? where item_id = ?"
        try:
            self.__conn.execute(stmt, (notes, item_id))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error updating notes for saved item {item_id}: {e}")

    def get_search_results(self, search_id, page=1, per_page=10):
        logging.info(f"Getting search results for search_id: {search_id}, page: {page}, per_page: {per_page}")
        offset = (page - 1) * per_page
        results = {'items': [], 'total': 0, 'pages': 0}
        try:
            # Get total count
            count_stmt = "select count(*) from search_results where search_id = ?"
            total = self.__conn.execute(count_stmt, (search_id,)).fetchone()[0]
            results['total'] = total
            results['pages'] = (total + per_page - 1) // per_page

            # Get paginated items
            stmt = "select item_json, skipped from search_results where search_id = ? order by rowid desc limit ? offset ?"
            for row in self.__conn.execute(stmt, (search_id, per_page, offset)):
                results['items'].append({'item_json': row[0], 'skipped': row[1]})
        except Exception as e:
            logging.error(f"Error getting search results for search {search_id}: {e}")
        return results

    def delete_saved_item(self, item_id):
        stmt = "delete from saved_items where item_id = ?"
        try:
            self.__conn.execute(stmt, (item_id,))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting saved item with id {item_id}: {e}")

    def get_all_saved_items(self) -> List[Item]:
        stmt = "select item_id, chat_id, title, price, url, publish_date, description, item, notes from saved_items"
        items = []
        try:
            for row in self.__conn.execute(stmt):
                items.append(Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))
        except Exception as e:
            logging.error(f"Error getting all saved items: {e}")
        return items

    def add_saved_item(self, item: Item):
        stmt = "insert into saved_items (item_id, chat_id, title, price, description, url, publish_date, item, notes) " \
               "values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        args = (item.item_id, item.chat_id, item.title, item.price, item.description, item.url, item.publish_date, item.item, item.notes)
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"Item already exists in saved_items: {item.item_id}")
            raise

    def add_search(self, chat_search):
        stmt = "insert into chat_search (chat_id, kws"
        valu = " values (?, ?"
        args = (chat_search.chat_id, chat_search.kws)
        if chat_search.cat_ids is not None:
            stmt += ", cat_ids"
            valu += ", ?"
            args += (chat_search.cat_ids,)
        if chat_search.min_price is not None:
            stmt += ", min_price"
            valu += ", ?"
            args += (chat_search.min_price,)
        if chat_search.max_price is not None:
            stmt += ", max_price"
            valu += ", ?"
            args += (chat_search.max_price,)
        if chat_search.dist is not None:
            stmt += ", dist"
            valu += ", ?"
            args += (chat_search.dist,)
        if chat_search.publish_date is not None:
            stmt += ", publish_date"
            valu += ", ?"
            args += (chat_search.publish_date,)
        if chat_search.orde is not None:
            stmt += ", ord"
            valu += ", ?"
            args += (chat_search.orde,)
        if chat_search.username is not None:
            stmt += ", username"
            valu += ", ?"
            args += (chat_search.username,)
        if chat_search.name is not None:
            stmt += ", name"
            valu += ", ?"
            args += (chat_search.name,)
        if chat_search.active is not None:
            stmt += ", active"
            valu += ", ?"
            args += (chat_search.active,)
        stmt += ")" + valu + ")"
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except sqlite3.IntegrityError as e:
            logging.error(f"Error adding chat search: {e}")

    def add_item(self, item_id, chat_id, title, price, url, user, publish_date=None, description=None, notes=None):
        stmt = "insert into item (itemId, chatId, title, price, url, user, publishDate, description, notes) " \
               "values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        args = (item_id, chat_id, title, price, url, user, publish_date, description, notes)
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error adding item: {e}")

    def update_item(self, item_id, price, description, notes):
        stmt = "update item " \
               "set price = ?, " \
               "description = ?, " \
               "notes = ? " \
               "where itemId = ?"
        try:
            self.__conn.execute(stmt, (price, description, notes, item_id))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error updating item: {e}")

    def delete_items(self, hours_live):
        millis = int(round(time.time() * 1000))
        millis -= hours_live * 60 * 60 * 1000
        stmt = "delete from item where publishDate < (?)"
        args = (millis,)
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting items older than {hours_live} hours: {e}")

    def search_item(self, item_id, chat_id):
        stmt = "select itemId, chatId, title, price, url, publishDate, description, user, notes " \
               "from item where itemId = (?) and chatId = (?)"
        args = (item_id, chat_id)
        try:
            for row in self.__conn.execute(stmt, args):
                i = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                return i
        except Exception as e:
            logging.error(f"Error searching item: {e}")
        return None

    def get_chat_searches(self, chat_id):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord from chat_search " \
               "where chat_id = ? and active = 1"
        searches = []
        try:
            for row in self.__conn.execute(stmt, (chat_id,)):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                searches.append(c)
        except Exception as e:
            logging.error(f"Error getting chat searches for chat_id {chat_id}: {e}")
        return searches

    def get_chats_searches(self):
        # Select the rowid as the unique identifier for the search
        stmt = "select rowid, chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord from chat_search " \
               "where active = 1"
        lista: List[ChatSearch] = []
        try:
            for row in self.__conn.execute(stmt):
                c = ChatSearch(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                c.id = row[0]  # Assign the rowid to the 'id' attribute
                lista.append(c)
        except Exception as e:
            logging.error(f"Error getting all chat searches: {e}")

            # for i in lista:
            #     logging.debug(f"Chat: {i.chat_id} - Keywords: {i.kws} - Categories: {i.cat_ids} - "
            #                   f"Min price: {i.min_price} - Max price: {i.max_price} - "
            #                   f"Distance: {i.dist} - Publish date: {i.publish_date} - Order: {i.orde}")

        return lista

    def remove_search(self, search_id):
        """Deactivates a search using its unique rowid."""
        stmt = "update chat_search set active = 0 where rowid = ?"
        try:
            self.__conn.execute(stmt, (search_id,))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deactivating search with id {search_id}: {e}")

    def del_chat_search(self, chat_id, kws):
        stmt = "update chat_search set active = 0 where chat_id = ? and kws = ?"
        try:
            self.__conn.execute(stmt, (chat_id, kws))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting chat search for chat_id {chat_id} and kws {kws}: {e}")
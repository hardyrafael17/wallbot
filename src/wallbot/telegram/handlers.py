import textwrap
from re import sub
from telegram.ext import CommandHandler
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.database.models import ChatSearch

class TelegramHandlers:
    def __init__(self, application, db: DBHelper):
        self.application = application
        self.db = db
        self._register_handlers()

    def _register_handlers(self):
        self.application.add_handler(CommandHandler(['start', 'help', 's', 'h'], self.send_welcome))
        self.application.add_handler(CommandHandler(['add', 'append', 'a'], self.add_search))
        self.application.add_handler(CommandHandler(['del', 'd'], self.delete_search))
        self.application.add_handler(CommandHandler(['lis', 'l'], self.get_searches))

    def send_welcome(self, update, context):
        welcome_text = textwrap.dedent("""
            *Utilización*
            /help
            *Añadir búsquedas:*
            	/add `búsqueda,min-max`
            	/add zapatos rojos,5-25
            *Borrar búsqueda:*
            	/del `búsqueda`
            	/del zapatos rojos
            *Lista de búsquedas:*
            	/lis
        """)
        update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def add_search(self, update, context):
        cs = ChatSearch()
        cs.chat_id = update.message.chat_id
        parameters = str(update.message.text).split(' ', 1)
        if len(parameters) < 2:
            return
        token = ' '.join(parameters[1:]).split(',')
        if len(token) < 1:
            return
        cs.kws = token[0].strip()
        if len(token) > 1:
            rango = token[1].split('-')
            cs.min_price = rango[0].strip()
            if len(rango) > 1:
                cs.max_price = rango[1].strip()
        if len(token) > 2:
            cs.cat_ids = sub(r'\s+', '', ','.join(token[2:]))
            if len(cs.cat_ids) == 0:
                cs.cat_ids = None
        cs.username = update.message.from_user.username
        cs.name = update.message.from_user.first_name
        cs.active = 1
        self.db.add_search(cs)

    async def delete_search(self, update, context):
        parameters = str(update.message.text).split(' ', 1)
        if len(parameters) < 2:
            return
        self.db.del_chat_search(update.message.chat_id, ' '.join(parameters[1:]))

    async def get_searches(self, update, context):
        text = ''
        for chat_search in self.db.get_chat_searches(update.message.chat_id):
            if len(text) > 0:
                text += '\n'
            text += chat_search.kws
            text += '|'
            if chat_search.min_price is not None:
                text += chat_search.min_price
            text += '-'
            if chat_search.max_price is not None:
                text += chat_search.max_price
            if chat_search.cat_ids is not None:
                text += '|'
                text += chat_search.cat_ids
        if len(text) > 0:
            await update.message.reply_text(text)

import logging
from telegram.ext import Application
from src.wallbot.config.settings import TOKEN

def create_application():
    logging.info("Creating application...")
    application = Application.builder().token(TOKEN).build()
    return application

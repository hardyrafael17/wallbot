import locale
import logging
import sys
from logging.handlers import RotatingFileHandler
import coloredlogs

from src.wallbot.config.settings import PROFILE


def setup_logger():
    log_path = 'wallbot.log'
    level = logging.DEBUG

    if PROFILE is None:
        log_path = '/logs/' + log_path
        level = logging.INFO
        # Configuración solo con archivo cuando PROFILE no está definido
        logging.basicConfig(
            handlers=[RotatingFileHandler(log_path, maxBytes=1000000, backupCount=10)],
            level=level,
            format='%(asctime)s %(filename)s:%(lineno)d %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S'
        )
    else:
        # Configuración con archivo y salida estándar cuando PROFILE está definido
        coloredlogs.install(
            level=level,
            stream=sys.stdout,
            fmt='%(filename)s:%(lineno)d - %(message)s',
            field_styles={
                'filename': {'color': 'magenta'},
                'lineno': {'color': 'blue'},
                'message': {'color': 'white'}
            },
            level_styles={
                'debug': {'color': 'cyan'},
                'info': {'color': 'green'},
                'warning': {'color': 'yellow'},
                'error': {'color': 'red'},
                'critical': {'color': 'red', 'bold': True}
            }
        )
        logging.basicConfig(
            handlers=[
                RotatingFileHandler(log_path, maxBytes=1000000, backupCount=10)
            ],
            level=level,
            format='%(asctime)s %(filename)s:%(lineno)d %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S'
        )

    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("telegram").setLevel(logging.INFO)

    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        logging.warning("Could not set locale 'es_ES.UTF-8'. This might be due to the locale not being installed on the system.")
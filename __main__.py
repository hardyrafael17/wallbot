import logging
import threading
import asyncio
from src.wallbot.wallapop.search_monitor import check_saved_searches

def setup_logging():
    """Configures logging to be less verbose for libraries."""
    # Get the root logger and remove any existing handlers
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Configure the root logger with our settings
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s'
    )

    # Set the log level for your application's root module to DEBUG
    # This will show all your custom debug logs.
    logging.getLogger('src.wallbot').setLevel(logging.DEBUG)

    # Set higher logging levels for noisy libraries, including the telegram extension
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger('telegram.ext').setLevel(logging.WARNING)
    logging.getLogger('telegram.bot').setLevel(logging.WARNING)
    logging.getLogger("waitress").setLevel(logging.WARNING)

def run_web_server():
    """
    Starts the Flask web server in a production-ready way.
    """
    try:
        # Assuming your Flask app instance is named 'app' inside 'src.wallbot.web.app'
        from src.wallbot.web.app import app
        from waitress import serve
        logging.info("Starting web server on http://0.0.0.0:8080")
        serve(app, host='0.0.0.0', port=8080)
    except ImportError:
        logging.error("Web server application not found or could not be imported.")
        logging.error("Please make sure 'src/wallbot/web/app.py' exists and contains a Flask 'app'.")
    except Exception as e:
        logging.error(f"Failed to start web server: {e}")

async def main():
    """Main async function to run all services."""
    # Set up the custom logging configuration
    setup_logging()

    # Start the web server in a background thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Start the saved searches monitor
    # This will run indefinitely
    await check_saved_searches()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application shutting down.")
    except Exception as e:
        logging.critical(f"Application failed with a critical error: {e}", exc_info=True)
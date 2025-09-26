import logging
import threading

# Import the original main function and rename it for clarity
from .main import main as run_bot_logic
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.web.app import create_web_app
from src.wallbot.utils.logger import setup_logger

def run_web_server():
    """
    Starts the Flask web server in a production-ready way using Waitress.
    """
    try:
        # Create a DBHelper instance
        db = DBHelper()
        # Create the Flask app using the factory function
        app = create_web_app(db)
        
        from waitress import serve
        logging.info("Starting web server on http://0.0.0.0:8080")
        # Use waitress to serve the app. It's a production-ready WSGI server.
        serve(app, host='0.0.0.0', port=8080)
    except ImportError:
        logging.error("Web server application not found or could not be imported.")
        logging.error("Please make sure 'src/wallbot/web/app.py' exists and contains a Flask 'app'.")
    except Exception as e:
        logging.error(f"Failed to start web server: {e}")


if __name__ == "__main__":
    setup_logger()
    # Start the web server in a non-blocking background thread.
    # The 'daemon=True' flag ensures the thread will exit when the main program exits.
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Run the main bot application logic in the main thread.
    # This is a blocking call that will keep the application alive.
    try:
        run_bot_logic()
    except Exception as e:
        logging.critical(f"The core bot application has crashed: {e}", exc_info=True)

    logging.info("Application has shut down.")

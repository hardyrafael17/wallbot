import asyncio
import json
import logging
import websockets
from src.wallbot.database.requests_db_helper import RequestsDBHelper

async def handler(websocket, path):
    db_helper = RequestsDBHelper()
    async for message in websocket:
        try:
            data = json.loads(message)
            logging.info(f"Received data: {data}")
            db_helper.add_request(data)
            await websocket.send(json.dumps({"status": "success", "message": "Data saved"}))
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from message.")
            await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON format"}))
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            await websocket.send(json.dumps({"status": "error", "message": str(e)}))

def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(handler, "localhost", 8765)
    logging.info("Starting WebSocket server on ws://localhost:8765")
    loop.run_until_complete(start_server)
    loop.run_forever()

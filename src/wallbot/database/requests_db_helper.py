import json
import logging
import sqlite3
from typing import List, Dict, Any

class RequestsDBHelper:
    def __init__(self, dbname="data/request_and_responses.sqlite"):
        self.__conn = sqlite3.connect(dbname, timeout=15, check_same_thread=False)
        self.setup()

    def setup(self):
        tblstmt = """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            method TEXT NOT NULL,
            status INTEGER NOT NULL,
            headers TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.__conn.execute(tblstmt)
        self.__conn.commit()

    def add_request(self, data: Dict[str, Any]):
        headers_str = json.dumps(data.get("headers", []))
        response_str = json.dumps(data.get("response", {}))
        
        stmt = """
        INSERT INTO requests (url, method, status, headers, response)
        VALUES (?, ?, ?, ?, ?)
        """
        args = (
            data.get("url"),
            data.get("method"),
            data.get("status"),
            headers_str,
            response_str,
        )
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error adding request: {e}")

    def get_all_requests(self) -> List[Dict[str, Any]]:
        stmt = "SELECT id, url, method, status, headers, response, timestamp FROM requests ORDER BY timestamp DESC"
        requests = []
        try:
            for row in self.__conn.execute(stmt):
                requests.append({
                    "id": row[0],
                    "url": row[1],
                    "method": row[2],
                    "status": row[3],
                    "headers": json.loads(row[4]),
                    "response": json.loads(row[5]),
                    "timestamp": row[6]
                })
        except Exception as e:
            logging.error(f"Error getting all requests: {e}")
        return requests

    def delete_all_requests(self):
        stmt = "DELETE FROM requests"
        try:
            self.__conn.execute(stmt)
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting all requests: {e}")

import sqlite3
import os
from typing import Any, Dict, List
from app.db import DatabaseClient
from app.config.settings import settings
from app.utils.logger import logger


class SqlClient(DatabaseClient):
    def __init__(self, db_path: str):
        self.db_path = f"{settings.SQLITE_DB_PATH}/{db_path}"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def execute_commands(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple SQLite commands and return results"""
        results = {}
        for query in queries:
            name = query['name']
            query = query['query']
            self.cursor.execute(query)

            if query.startswith("SELECT"):
                results[name] = self.cursor.fetchall()  # Key by query for SELECT
            else:
                self.conn.commit()  # Commit changes for non-SELECT commands
                results[name] = "Command executed"  # Simple success for non-SELECT

        return results

    def get_schema(self) -> List[str]:
        """Return the DB schema"""
        self.cursor.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"
        )
        schema_info = self.cursor.fetchall()
        schema_list = []
        for row in schema_info:
            schema_list.append(f"Type: {row[0]}, Name: {row[1]}, SQL: {row[2]}")
        return schema_list

    def is_initialized(self) -> bool:
        """Check if the database has been initialized"""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = self.cursor.fetchall()
        return len(tables) > 0

    def mark_initialized(self) -> None:
        pass


# Create global SQLite client instance
sql_client = SqlClient()

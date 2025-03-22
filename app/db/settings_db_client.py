import sqlite3
from app.utils.logger import logger
from app.config.settings import settings

SETTINGS_TABLE_NAME = "app_settings"
PAGE_INSTRUCTIONS_TABLE_NAME = "page_instructions"

class SettingsDBClient:
    def __init__(self, db_path: str = settings.SQLITE_SETTINGS_DB_PATH):
        self.db_path = db_path
        self.conn = None

    def _connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def _close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    async def initialize_db(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SETTINGS_TABLE_NAME} (
                application_type TEXT,
                prompt_template TEXT,
                guid TEXT
            )
        """)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {PAGE_INSTRUCTIONS_TABLE_NAME} (
                page_path TEXT PRIMARY KEY,
                page_instructions TEXT,
                guid TEXT
            )
        """)
        conn.commit()
        self._close()

    def get(self, guid: str, page_path: str) -> dict[str, str] | None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT application_type, prompt_template, guid FROM {SETTINGS_TABLE_NAME} WHERE guid = ? LIMIT 1", (guid,))
        settings_row = cursor.fetchone()
        cursor.execute(f"SELECT page_instructions FROM {PAGE_INSTRUCTIONS_TABLE_NAME} WHERE page_path = ? AND guid = ? LIMIT 1", (page_path, guid))
        page_instructions_row = cursor.fetchone()
        if not page_instructions_row:
            page_instructions_row = [""]
        self._close()
        return {"application_type": settings_row[0], "prompt_template": settings_row[1], "page_instructions": page_instructions_row[0]}

    def update(self, guid: str, application_type: str, prompt_template: str, page_instructions: str, page_path: str):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                REPLACE INTO {SETTINGS_TABLE_NAME} (application_type, prompt_template, guid)
                VALUES (?, ?, ?)
            """, (application_type, prompt_template, guid))
            cursor.execute(f"""
                REPLACE INTO {PAGE_INSTRUCTIONS_TABLE_NAME} (page_path, page_instructions, guid)
                VALUES (?, ?, ?)
            """, (page_path, page_instructions, guid))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback() # Rollback in case of error
        finally:
            self._close()

settings_db_client = SettingsDBClient(settings.SQLITE_SETTINGS_DB_PATH)
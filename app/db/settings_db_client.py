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

    def initialize_db(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SETTINGS_TABLE_NAME} (
                application_type TEXT,
                prompt_template TEXT
            )
        """)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {PAGE_INSTRUCTIONS_TABLE_NAME} (
                page_path TEXT PRIMARY KEY,
                page_instructions TEXT
            )
        """)
        cursor.execute(f"SELECT count(*) FROM {SETTINGS_TABLE_NAME}")
        settings_count = cursor.fetchone()[0]
        if settings_count == 0:
            default_application_type = settings.APPLICATION_TYPE
            default_prompt_template = settings.RESPONSE_PROMPT
            cursor.execute(f"""
                INSERT INTO {SETTINGS_TABLE_NAME} (application_type, prompt_template)
                VALUES (?, ?)
            """, (default_application_type, default_prompt_template))
        cursor.execute(f"SELECT count(*) FROM {PAGE_INSTRUCTIONS_TABLE_NAME}")
        page_instructions_count = cursor.fetchone()[0]
        if page_instructions_count == 0:
            default_page_path = "/" # Default page path
            cursor.execute(f"""
                INSERT INTO {PAGE_INSTRUCTIONS_TABLE_NAME} (page_path, page_instructions)
                VALUES (?, ?)
            """, (default_page_path, "")) # Initialize page_instructions to empty string
        conn.commit()
        self._close()

    def get_settings(self, page_path: str) -> dict[str, str] | None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT application_type, prompt_template FROM {SETTINGS_TABLE_NAME} LIMIT 1")
        settings_row = cursor.fetchone()
        cursor.execute(f"SELECT page_instructions FROM {PAGE_INSTRUCTIONS_TABLE_NAME} WHERE page_path = ? LIMIT 1", (page_path,))
        page_instructions_row = cursor.fetchone()
        self._close()
        return {"application_type": settings_row[0], "prompt_template": settings_row[1], "page_instructions": page_instructions_row[0] or ""}

    def update_settings(self, application_type: str, prompt_template: str, page_instructions: str, page_path: str):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {SETTINGS_TABLE_NAME}") # Simple replace strategy for application settings
            cursor.execute(f"""
                INSERT INTO {SETTINGS_TABLE_NAME} (application_type, prompt_template)
                VALUES (?, ?)
            """, (application_type, prompt_template))
            cursor.execute(f"DELETE FROM {PAGE_INSTRUCTIONS_TABLE_NAME} WHERE page_path = ?", (page_path,)) # Delete page instructions based on page_path
            cursor.execute(f"""
                INSERT INTO {PAGE_INSTRUCTIONS_TABLE_NAME} (page_path, page_instructions)
                VALUES (?, ?)
            """, (page_path, page_instructions)) # Insert new page instructions
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback() # Rollback in case of error
        finally:
            self._close() 

settings_db_client = SettingsDBClient()
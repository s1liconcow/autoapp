import sqlite3
from app.utils.logger import logger
from app.config.settings import settings

SETTINGS_TABLE_NAME = "app_settings"
PAGE_INSTRUCTIONS_TABLE_NAME = "page_instructions"
GENERATED_TEMPLATES_TABLE_NAME = "generated_templates"

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
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {GENERATED_TEMPLATES_TABLE_NAME} (
                guid TEXT,
                page_path TEXT,
                template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guid, page_path)
            )
        """)
        conn.commit()
        self._close()

    def get(self, guid: str, page_path: str, referring_page: str | None = None) -> dict[str, str] | None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT application_type, prompt_template, guid FROM {SETTINGS_TABLE_NAME} WHERE guid = ? LIMIT 1", (guid,))
        settings_row = cursor.fetchone()
        cursor.execute(f"SELECT page_instructions FROM {PAGE_INSTRUCTIONS_TABLE_NAME} WHERE page_path = ? AND guid = ? LIMIT 1", (page_path, guid))
        page_instructions_row = cursor.fetchone()
        
        # First try to get template for current page
        cursor.execute(f"SELECT template FROM {GENERATED_TEMPLATES_TABLE_NAME} WHERE guid = ? AND page_path = ? ORDER BY created_at DESC LIMIT 1", (guid, page_path))
        template_row = cursor.fetchone()
        using_referring_page = False
        
        # If no template found and referring page is provided, try to get template from referring page
        if not template_row and referring_page:
            cursor.execute(f"SELECT template FROM {GENERATED_TEMPLATES_TABLE_NAME} WHERE guid = ? AND page_path = ? ORDER BY created_at DESC LIMIT 1", (guid, referring_page))
            template_row = cursor.fetchone()
            using_referring_page = True
            

        if not page_instructions_row:
            page_instructions_row = [""]
        if not template_row:
            template_row = [""]
        if not settings_row:
            return None
        self._close()
        return {
            "application_type": settings_row[0], 
            "prompt_template": settings_row[1], 
            "page_instructions": page_instructions_row[0],
            "generated_template": template_row[0],
            "guid": guid,
            "using_referring_page": using_referring_page    
        }

    def update(self, guid: str, application_type: str, prompt_template: str, page_instructions: str, page_path: str, generated_template: str = None):
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
            if generated_template:
                cursor.execute(f"""
                    REPLACE INTO {GENERATED_TEMPLATES_TABLE_NAME} (guid, page_path, template)
                    VALUES (?, ?, ?)
                """, (guid, page_path, generated_template))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback() # Rollback in case of error
        finally:
            self._close()

    def clear_templates(self, guid: str, page_path: str = None):
        """Clear all generated templates for a given guid, optionally filtered by page_path"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            if page_path:
                cursor.execute(f"""
                    DELETE FROM {GENERATED_TEMPLATES_TABLE_NAME}
                    WHERE guid = ? AND page_path = ?
                """, (guid, page_path))
            else:
                cursor.execute(f"""
                    DELETE FROM {GENERATED_TEMPLATES_TABLE_NAME}
                    WHERE guid = ?
                """, (guid,))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
        finally:
            self._close()

settings_db_client = SettingsDBClient(settings.SQLITE_SETTINGS_DB_PATH)
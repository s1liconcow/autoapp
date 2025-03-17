import json
import logging

from datetime import datetime
from typing import Dict, Any, List, Optional

from app.config.settings import settings
from app.llm.client import llm_client
from app.db import DatabaseClient

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    def __init__(
        self,
        db_client: DatabaseClient
    ):
        self.db_client = db_client

    async def initialize_database(self):
        """Initialize Redis with sample data from LLM"""
        # Check if database is already initialized
        if self.db_client.is_initialized():
            logger.info("Database already initialized, skipping initialization")
            return

        logger.info("Initializing database with sample data...")

        # Format the initialization prompt, including the data_model_key
        init_prompt = settings.INIT_PROMPT_TEMPLATE.format(
            application_type=settings.APPLICATION_TYPE,
            data_model_key=settings.DATA_MODEL_KEY,
        )

        logger.info(init_prompt)
        # Get the LLM response
        response_text = await llm_client.get_response(init_prompt)

        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        if not response_text.endswith("}"):
            response_text += "}"

        # Parse and execute initialization commands
        logger.info("Raw response: %s", response_text)
        init_data = json.loads(response_text)

        commands = init_data.get("commands", [])

        results = self.db_client.execute_commands(commands)

        # Mark database as initialized
        self.db_client.mark_initialized()

        logger.info("Database initialization complete")
        logger.debug("Initialization results: %s", results)

from typing import Optional
import requests
import anthropic
from google import genai
from app import db
from google.genai import types
from app.config.settings import settings
from app.utils.logger import logger
from app.db import settings_db_client


class LLMClient:
    def __init__(self):
        if settings.LLM_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.app_settings_db = settings_db_client.settings_db_client

    async def get_response(self, user: str, system: Optional[str] = None, *, strong_model: bool = False) -> str | None:
        """Get response from configured LLM provider"""
        if settings.LLM_PROVIDER == "gemini":
            config = types.GenerateContentConfig(
                system_instruction=system if system else None,
                response_mime_type="application/json",
                response_schema={
                    "properties": {
                        "template": {"type": "STRING"},
                        "CSS": {"type": "STRING"},
                        "Javascript": {"type": "STRING"},
                        "commands": {
                            "type": "array",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "name": {"type": "string"},
                                    "query": {"type": "string"},
                                }
                            }
                        }
                    },
                    "type": "OBJECT"
                }
            )
            contents=[user]
            if strong_model:
                logger.info("Using strong model!")
                contents = [system, user]
                config = None
            response = self.client.models.generate_content(
                model=settings.GEMINI_DESIGN_MODEL if strong_model else settings.GEMINI_MODEL,
                contents=contents,
                config=config 
            )
            return response.text

        elif settings.LLM_PROVIDER == "claude":
            client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=3000,
                system=[{"type": "text", "text": system}] if system else None,
                messages=[{"role": "user", "content": "{" + user}],
            )
            return response.content[0].text

        else:  # default to ollama
            response = requests.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": system + user,
                    "stream": False,
                    "format": {
                        "type": "object",
                        "properties": {
                            "redis_commands": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "command": {"type": "string"},
                                        "args": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                    },
                                    "required": ["command", "args"],
                                },
                            },
                            "template": {
                                "type": "string",
                            },
                            "CSS": {
                                "type": "string",
                            },
                            "Javascript": {
                                "type": "string",
                            },
                        },
                    },
                },
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )

    async def get_design_response(self, user: str, system: Optional[str] = None) -> str | None:
        """Get response from LLM using a more capable model for design-phase thinking"""
        if settings.LLM_DESIGN_PROVIDER == "gemini":
            # Use a more capable model for design
            design_model = settings.GEMINI_DESIGN_MODEL
            response = self.client.models.generate_content(
                model=design_model, contents=[user]
            )
            return response.text

        elif settings.LLM_DESIGN_PROVIDER == "claude":
            client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            # Use Claude-3 Opus for design phase
            design_model = settings.CLAUDE_MODEL_DESIGN
            
            response = client.messages.create(
                model=design_model,
                max_tokens=4000,
                system=[{"type": "text", "text": system}] if system else None,
                messages=[{"role": "user", "content": "{" + user}],
            )
            return response.content[0].text

        else: 
            raise NotImplementedError("Design mode not available for ollama :(")

    def format_prompt(self, data_model: str, app_settings: dict) -> str:
        """Format the prompt with system context and user message"""
        per_page_settings = ""
        if app_settings['page_instructions']:
            per_page_settings = f"Page specific instructions:\n{app_settings['page_instructions']}"

        previous_template = ""
        if app_settings.get('generated_template'):
            template_source = "for this page" if not app_settings.get('using_referring_page') else "for the referring page"
            previous_template = f"""
            Previously generated template (from {template_source}):
            ```html
            {app_settings['generated_template']}
            ```
            Please maintain asthetic consistency necessary for the current request but be sure to replace all static data with database calls. 
            """

        system_prompt = f"""
        You are a modern world-class full featured web application server. 

        Application Description: 
        {app_settings['application_type']}

        Your data model is:
        {data_model}

        {app_settings['prompt_template']}

        {per_page_settings}

        {previous_template}

        The application is mounted at /{app_settings['guid']}.  All links should include the guid and be relative to this path.
        """

        return system_prompt


# Create global LLM client instance
llm_client = LLMClient()

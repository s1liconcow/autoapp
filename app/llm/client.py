from typing import Optional
import requests
from google import genai
from google.genai import types
from app.config.settings import settings
from app.utils.logger import logger

class LLMClient:
    def __init__(self):
        if settings.LLM_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def get_response(self, prompt: str) -> str:
        """Get response from configured LLM provider"""
        if settings.LLM_PROVIDER == "gemini":
            config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        'properties': {
                            'template': {'type': 'STRING'},
                            'redis_commands': {
                                'type': 'array',
                                'items': {
                                    'type': 'OBJECT',
                                    'properties': {
                                        'command': {'type': 'string'},
                                        'args': {'type': 'array', 'items': {'type': 'string'}}
                                    },
                                    'required': ['command', 'args']
                                }
                            }
                        },
                        'type': 'OBJECT'
                    }
                )
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=config
            )
            return response.text
            
        else:  # default to ollama
            response = requests.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
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
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "required": ["command", "args"]
                                }
                            },
                            "template": {
                                "type": "string",
                            }
                        },
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

    def format_prompt(self, user_message: str, data_model: str, redis_keys: str = None) -> str:
        """Format the prompt with system context and user message"""
        system_prompt = f"""
        You are a modern world-class full featured {settings.APPLICATION_TYPE} web application.
        
        Your data model is:
        {data_model}

        {settings.REDIS_COMMANDS_HELP}

        {settings.RESPONSE_PROMPT}
        """

        if redis_keys:
            system_prompt += "\nExisting Redis Keys:\n" + f"\n{redis_keys}"

        return f"System: {system_prompt}\n\nUser Request: {user_message}\n\nAssistant:"

# Create global LLM client instance
llm_client = LLMClient()

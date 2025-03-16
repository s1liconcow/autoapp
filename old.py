from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import redis
from typing import Optional
from datetime import datetime, timedelta
import logging
import os

from app.config.settings import settings
from app.db.redis_client import redis_client
from app.llm.client import get_llm_response
from app.llm.database_init import DatabaseInitializer

# Configure logging with more detailed format in dev mode
logging.basicConfig(
    level=logging.DEBUG if settings.DEV_MODE else logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s' if settings.DEV_MODE else '%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('llm_interactions.log')
    ]
)
logger = logging.getLogger(__name__)

# Log startup configuration
logger.info("Starting application in %s mode", "development" if settings.DEV_MODE else "production")

app = FastAPI(
    title=settings.APPLICATION_TITLE,
    description=settings.APPLICATION_DESCRIPTION,
    version="1.0.0",
    debug=settings.DEV_MODE
)
templates = Jinja2Templates(directory="templates")

# Initialize database initializer
db_initializer = DatabaseInitializer(redis_client, settings.DATA_MODEL, settings.APPLICATION_TYPE)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request,}
    )

@app.post("/update_prompt")
async def update_prompt(prompt: str = Form(...)):
    prompt = settings.CURRENT_PROMPT
    all_keys = redis_client.keys("*")
    keys_str = "\nExisting Redis Keys:\n" + "\n".join(sorted(all_keys))
    
    # Update the prompt with the current Redis keys
    prompt = prompt + keys_str
    return {"status": "success", "prompt": prompt}

@app.post("/get_response", response_class=HTMLResponse)
async def get_response(message: str = Form(...)):
    try:
        prompt = settings.CURRENT_PROMPT
        all_keys = redis_client.keys("*")
        keys_str = "\nExisting Redis Keys:\n" + "\n".join(sorted(all_keys))
        
        # Update the prompt with the current Redis keys
        prompt = prompt + keys_str
        prompt = f"System: {prompt}\n\nUser: {message}\n\nAssistant:"
        logger.info("\n=== LLM Request ===\n%s\n==================", prompt)
        
        response_text = await get_llm_response(prompt)
        
        # Strip ```json markers if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        if not response_text.endswith("}"):
            response_text += "}"
        
        logger.info("\n=== LLM Response ===\n%s\n==================", response_text)
        
        try:
            # Parse the JSON response
            llm_response = json.loads(response_text)
            
            # Execute Redis commands
            redis_results = db_initializer.execute_redis_commands(llm_response.get("redis_commands", []))
            
            # Prepare template context
            context = {
                "request": {"url": message},
                "redis_results": redis_results,
            }
            
            # Render the template
            template = templates.env.from_string(llm_response["template"])
            rendered_html = template.render(**context)
            return rendered_html
            
        except json.JSONDecodeError as json_error:
            logger.error("JSON parsing error: %s", str(json_error))
            return f"""
            <div class='error'>
                <p><strong>Invalid JSON Response:</strong> {str(json_error)}</p>
                <hr>
                <p><strong>Raw Response:</strong></p>
                <pre>{response_text}</pre>
            </div>
            """
        except Exception as template_error:
            logger.error("Template rendering error: %s", str(template_error))
            return f"""
            <div class='error'>
                <p><strong>Template Error:</strong> {str(template_error)}</p>
                <hr>
                <p><strong>LLM Response:</strong></p>
                <pre>{response_text}</pre>
            </div>
            """
    except Exception as e:
        # Log unexpected errors
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return f"""
        <div class='error'>
            <p><strong>Error:</strong> {str(e)}</p>
            <hr>
            <p><strong>Request:</strong></p>
            <pre>{message}</pre>
        </div>
        """

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn_config = {
        "app": "app:app",  # Import string for the application
        "host": "0.0.0.0",
        "port": 8000,
        "reload": settings.DEV_MODE,  # Auto-reload on file changes in dev mode
        "reload_dirs": ["templates"] if settings.DEV_MODE else None,  # Watch template directory for changes
        "workers": 1 if settings.DEV_MODE else 2,  # Single worker in dev mode for easier debugging
        "log_level": "debug" if settings.DEV_MODE else "info",
    }
    
    logger.info("Server starting with config: %s", uvicorn_config)
    uvicorn.run(**uvicorn_config) 
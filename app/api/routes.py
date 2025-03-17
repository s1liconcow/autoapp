from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json

from app.config.settings import settings
from app.db import DatabaseClient, redis_client
from app.db import sql_client
from app.llm.client import llm_client
from app.utils.logger import logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/get_response", response_class=HTMLResponse)
async def get_response(message: str = Form(...), db_type: str = Form("redis")):
    db_type = settings.DB_TYPE
    db_client: DatabaseClient 
    if db_type == "sql":
        db_client = sql_client.sql_client
    else:
        db_client = redis_client.redis_client
    
    try:
        data_model = db_client.get_schema()
        # Format prompt with system context and user message
        system_prompt = llm_client.format_prompt(
            data_model=data_model
        )

        logger.info(
            "\n=== LLM Request ===\n%s\n%s\n==================", system_prompt, message
        )

        # Get LLM response
        response_text = await llm_client.get_response(message, system_prompt)

        # Clean up response text
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

            # Execute database commands based on the selected client
            db_commands = llm_response.get("commands", [])
            db_results = db_client.execute_commands(db_commands)

            # Prepare template context
            context = {
                "request": {"url": message},
                "results": db_results,
                "db": db_client,
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
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

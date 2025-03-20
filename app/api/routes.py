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


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path: str):
    db_type = settings.DB_TYPE
    db_client: DatabaseClient
    if db_type == "sql":
        db_client = sql_client.sql_client
    else:
        db_client = redis_client.redis_client

    method = request.method
    path_url = request.url.path # Use request.url.path to get the path
    message_content = f"{method} {path_url}"
    if method != "GET": # Include body for non-GET requests
        try:
            body = await request.body()
            body_str = body.decode('utf-8')
            if body_str:
                message_content += f"\n{body_str}" # Append body to message
        except Exception as e:
            logger.warning(f"Could not read request body: {e}")


    try:
        data_model = db_client.get_schema()
        # Format prompt with system context and user message
        system_prompt = llm_client.format_prompt(
            data_model=data_model
        )

        logger.info(
            "\n=== Catch-all LLM Request ===\n%s\n%s\n==================", system_prompt, message_content
        )

        # Get LLM response
        response_text = await llm_client.get_response(message_content, system_prompt)

        # Clean up response text
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        if not response_text.endswith("}"):
            response_text += "}"

        logger.info("\n=== Catch-all LLM Response ===\n%s\n==================", response_text)

        try:
            # Parse the JSON response
            llm_response = json.loads(response_text)

            # Execute database commands based on the selected client
            db_commands = llm_response.get("commands", [])
            db_results = db_client.execute_commands(db_commands)

            # Prepare template context
            context = {
                "request": request,
                "results": db_results,
                "db": db_client,
            }

            # Render the template from LLM response
            llm_template = templates.env.from_string(llm_response["template"])
            rendered_html = llm_template.render(**context)

            # Render the index.html template, injecting the rendered_html into the body
            return templates.TemplateResponse(
                "index.html", {"request": request, "body": rendered_html}
            )

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
        logger.error("Unexpected error in catch-all route: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import uuid
from app.config.settings import settings
from app.db.settings_db_client import settings_db_client
from app.db import sql_client
from app.llm import database_init
from app.llm.client import llm_client
from app.utils.logger import logger
from bs4 import BeautifulSoup

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.api_route("/update_settings", methods=["POST"])
async def update_settings(
    request: Request,
    application_type: str = Form(...),
    page_instructions: str = Form(None),
    path: str = Form(None),
):
    logger.info(f"Updating settings with page_instructions: {page_instructions}")
    guid = path.split('/')[1]
    path = "/"+"/".join(path.split('/')[2:]) if len(path.split('/')) > 1 else "/"
    logger.info(f"Updating page settings for: {path}")

    settings_db_client.update(guid, application_type, settings.RESPONSE_PROMPT, page_instructions, path) # Persist settings to DB

    return RedirectResponse(guid+"/"+path, status_code=303) # Redirect back to homepage

@router.post("/")
async def root_post(request: Request, application_type: str = Form(...)):
    guid = uuid.uuid4()
    guid_str = str(guid)
    settings_db_client.update(guid_str, application_type, settings.RESPONSE_PROMPT, "", "/") # Persist settings to DB
    return RedirectResponse("/" + guid_str, status_code=303)

@router.get("/")
async def root_get(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "body":  """
            <div>
                <form method="post" action="/" class="">
                    <div>
                        <label class="block mb-2 text-sm font-bold text-gray-700">Application Type</label>
                        <input type="text" name="application_type" placeholder="TODO"
                            class="input input-bordered w-full max-w-xs"
                            value="TODO" />
                    </div>
                    <button class="btn btn-primary" type="submit">Create App</button>
                </form>
            </div>
        """, "app_settings": {"application_type": "TODO"}}
    )

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path: str):
    guid = None
    flash_message = None
    if path and path == "favicon.ico": # ignore favicon requests
        return

    guid = path.split('/')[0]
    if not guid:
        raise HTTPException(status_code=400, detail="GUID is missing from the path")
    path = "/"+"/".join(path.split('/')[1:]) if len(path.split('/')) > 1 else "/"

    app_settings = settings_db_client.get(guid, path)
    db_client = sql_client.SqlClient(f"{settings.SQLITE_DB_PATH}{guid}.db")
    if not db_client.is_initialized():
        # flash a notice that this will take a moment
        flash_message = "Database is initializing, this may take a moment."
        import asyncio
        app_type = app_settings['application_type']
        asyncio.create_task(database_init.DatabaseInitializer(db_client, app_type).initialize_database())
        context = {
            "flash_message": flash_message
        }

        # Render the index.html template, injecting the rendered_html into the body
        return templates.TemplateResponse(
            "app.html", {"request": request, "body": "", "app_settings": app_settings, "flash_message":flash_message}
        )

    method = request.method
    message_content = f"{method} {path}"
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
            data_model=data_model,
            app_settings=app_settings
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
                "flash_message": flash_message
            }

            # Render the template from LLM response
            llm_template = templates.env.from_string(llm_response["template"])
            rendered_html = llm_template.render(**context)

            # Find all links in the rendered HTML and preface them with /$guid/
            soup = BeautifulSoup(rendered_html, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if not href.startswith(('http://', 'https://', 'mailto:')):
                    a_tag['href'] = '/' + guid + '/' + href.lstrip('/')
            
            for form_tag in soup.find_all('form', action=True):
                action = form_tag['action'] 
                if not href.startswith(('http://', 'https://', 'mailto:')):
                    form_tag['action'] = '/' + guid + '/' + action.lstrip('/')

            rendered_html = str(soup)

            return templates.TemplateResponse(
                "app.html", {"request": request, "body": rendered_html, "app_settings": app_settings, "flash_message":flash_message}
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

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import uuid
from app.config.settings import settings
from app.db.settings_db_client import settings_db_client
from app.db import sql_client
from app.llm import app_init
from app.llm.client import llm_client
from app.utils.logger import logger
from bs4 import BeautifulSoup
import asyncio

router = APIRouter()
templates = Jinja2Templates(directory="templates")

initialization_locks = {}
initialized_guids = set()

@router.api_route("/update_settings", methods=["POST"])
async def update_settings(
    request: Request,
    application_type: str = Form(...),
    page_instructions: str = Form(None),
    path: str = Form(None),
    clear_templates: bool = Form(False)
):
    logger.info(f"Updating settings with page_instructions: {page_instructions}")
    guid = path.split('/')[1]
    path = "/"+"/".join(path.split('/')[2:]) if len(path.split('/')) > 1 else "/"
    logger.info(f"Updating page settings for: {path}")

    if clear_templates:
        settings_db_client.clear_templates(guid, path)  # Clear templates for this page

    settings_db_client.update(guid, application_type, settings.RESPONSE_PROMPT, page_instructions, path)  # Persist settings to DB

    return RedirectResponse(guid+"/"+path, status_code=303)  # Redirect back to homepage

@router.post("/")
async def root_post(request: Request, application_type: str = Form(...)):
    guid = uuid.uuid4()
    guid_str = str(guid)
    settings_db_client.update(guid_str, application_type, settings.RESPONSE_PROMPT, "", "/") # Persist settings to DB
    return RedirectResponse("/" + guid_str, status_code=303)

@router.get("/")
async def root_get(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path: str):
    # Extract the GUID from the path
    parts = path.split('/')
    guid = parts[0]
    path = "/" + "/".join(parts[1:]) if len(parts) > 1 else "/"
    
    # Get the referring page from request headers
    referer = request.headers.get("referer")
    referring_page = None
    if referer:
        # Extract the path from the full URL
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(referer)
            ref_path = parsed_url.path
            # Remove the guid prefix to get just the page path
            if ref_path and guid in ref_path:
                ref_parts = ref_path.split('/')
                if len(ref_parts) > 1 and ref_parts[1] == guid:
                    referring_page = "/" + "/".join(ref_parts[2:]) if len(ref_parts) > 2 else "/"
        except Exception as e:
            logger.warning(f"Error parsing referer: {e}")
    
    # Get settings for this application
    settings_data = settings_db_client.get(guid, path, referring_page)
    if not settings_data:
        raise HTTPException(status_code=404, detail="Application not found")

    # Initialize database client
    db_client = sql_client.SqlClient(f"{settings.SQLITE_DB_PATH}{guid}.db")
    
    # Handle database initialization if needed
    if not db_client.is_initialized():
        flash_message = "App is initializing, this may take a moment..."
        
        async def initialize_background():
            if guid in initialized_guids:
                return
            
            logger.info("Starting background design job for app: {}".format(guid))
                
            # Get or create a lock for this specific guid
            if guid not in initialization_locks:
                initialization_locks[guid] = asyncio.Lock()
            
            async with initialization_locks[guid]:
                # Double-check in case another task initialized while we were waiting
                if guid in initialized_guids:
                    return
                    
                app_type = settings_data['application_type']
                
                # Log design prompt request
                logger.info("\n=== Design Prompt Request ===\n%s\n==================", 
                          settings.DESIGN_PROMPT.format(app_type))
                punched_up_design = await llm_client.get_design_response(settings.DESIGN_PROMPT.format(app_type))
                logger.info("\n=== Design Prompt Response ===\n%s\n==================", 
                          punched_up_design)

                # Log template prompt request
                logger.info("\n=== Template Prompt Request ===\n%s\n==================", 
                          settings.DESIGN_TEMPLATE_PROMPT.format(punched_up_design))
                punched_up_template = await llm_client.get_design_response(settings.DESIGN_TEMPLATE_PROMPT.format(punched_up_design))
                logger.info("\n=== Template Prompt Response ===\n%s\n==================", 
                          punched_up_template)
                await app_init.AppInitializer(db_client, app_type).initialize_database()
                settings_db_client.update(guid, punched_up_design, settings.RESPONSE_PROMPT, "", "/", punched_up_template)

                
                initialized_guids.add(guid)
                initialization_locks.pop(guid, None)  # Clean up the lock
            
        # Create background task
        asyncio.create_task(initialize_background())
        
        # Return response immediately
        return templates.TemplateResponse(
            "app.html", {"request": request, "body": "", "app_settings": settings_data, "flash_message": flash_message}
        )

    # Prepare message content
    method = request.method
    message_content = f"{method} {path}"
    if method == "POST":
        try:
            body = await request.body()
            body_str = body.decode('utf-8')
            if body_str:
                message_content += f"\n{body_str}"
        except Exception as e:
            logger.warning(f"Could not read request body: {e}")

    try:
        # Get data model and format prompt
        data_model = db_client.get_schema()
        system_prompt = llm_client.format_prompt(
            data_model=data_model,
            app_settings=settings_data
        )

        logger.info(
            "\n=== Catch-all LLM Request ===\n%s\n%s\n==================", system_prompt, message_content
        )

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

            # Execute database commands if present
            db_results = None
            if "commands" in llm_response:
                db_results = db_client.execute_commands(llm_response["commands"])
                
                # Check for redirect command
                for cmd in llm_response["commands"]:
                    if "redirect" in cmd and cmd["redirect"]:
                        redirect_url = cmd["redirect"]
                        if not redirect_url.startswith(('http://', 'https://', '/')):
                            redirect_url = f"/{guid}/{redirect_url}"
                        elif redirect_url.startswith('/'):
                            redirect_url = f"/{guid}{redirect_url}"
                        return RedirectResponse(redirect_url, status_code=303)

            # Store and render template if present
            if "template" in llm_response:
                template = llm_response["template"]
                if template:
                    settings_db_client.update(guid, settings_data["application_type"], settings_data["prompt_template"], 
                                           settings_data["page_instructions"], path, template)

                # Prepare template context
                context = {
                    "request": request,
                    "results": db_results,
                    "db": db_client,
                    "path": path,
                }

                # Render template
                llm_template = templates.env.from_string(template)
                rendered_html = llm_template.render(**context)
                
                # Check if it's an HTMX request
                is_htmx = request.headers.get("HX-Request") == "true"
                
                if is_htmx:
                    return HTMLResponse(rendered_html)
                
                css, js = ("","")
                if "CSS" in llm_response:
                    css= llm_response['CSS']
                if "Javascript" in llm_response:
                    js = llm_response['Javascript']
                return templates.TemplateResponse(
                    "app.html",
                    {
                        "request": request,
                        "body": rendered_html,
                        "app_settings": settings_data,
                        "css": css,
                        "js": js
                    }
                )

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

        except json.JSONDecodeError:
            error_msg = "Invalid JSON response from LLM"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        logger.error("Unexpected error in catch-all route: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

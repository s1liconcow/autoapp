import os
from typing import Optional


class Settings:
    # Application Settings
    DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() == "true"
    APPLICATION_TYPE: str = os.getenv("APPLICATION_TYPE", "TODO")
    APPLICATION_TITLE: str = f"AI Powered {APPLICATION_TYPE}"
    APPLICATION_DESCRIPTION: str = os.getenv(
        "APPLICATION_DESCRIPTION", f"A world-class enterprise-grade {APPLICATION_TYPE}"
    )
    CLAUDE_MODEL: str = "claude-3-7-sonnet-20250219"
    CLAUDE_MODEL_DESIGN: str = "claude-3-7-sonnet-20250219"

    # Data Model
    DATA_MODEL_KEY: str = "data_model"
    # Prompts
    #
    SQL_PROMPT_TEMPLATE: str = """
    We are building a full-featured, modern, AI-enabled web application.
    
    Application Description:
    {application_type} 

    Generate sample data for the app using SQLite.
    First suggest a database schema and generate insert sample data into each table.  Use enough sample data to make a convincing application.
    The user table should contain the default user_id "user1" with username "default_user", and email "default@example.com"
     
    Example response format for SQLite:
    {{
        "commands": [
            {{"type": "sql", "name": "create_table_users", "query": "CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT, email TEXT)"}},
            {{"type": "sql", "name": "insert_user_1", "query": "INSERT INTO users (user_id, username, email) VALUES ('1', 'john_doe', 'john.doe@example.com') "}},
            {{"type": "sql", "name": "insert_user_2", "query": "INSERT INTO users (user_id, username, email) VALUES ('2', 'jane_doe', 'jane.doe@example.com') "}},
        ],
    }}

    REPLY ONLY WITH VALID JSON. Do not provide any improvements or explanations.
    """
    INIT_PROMPT_TEMPLATE = SQL_PROMPT_TEMPLATE

    SQL_RESPONSE_PROMPT: str = """
    You can query sqlite and render a Jinja template for the user as well as include css or javascript for rich interaction.

    * You should provide a beautiful and engaging user experience to the user.
    * Add beautiful headers and footers if appropriate for the described app.
    * All app pages should have navigation to other relevant pages.
    * You can create relative links to other pages that make sense for your type of application.
    * The result of sql commands will be available in a 'results' dictionary with the command's name as the key.
        For example "results['query_active_users']" returns a list of tuples (rows).
    * The Jinja template only has access to the results dictionary, all SQL queries must be completed ahead of time.
    * Tailwind CSS is already included and available, you don't need to load it.
    * HTMX is also included,  you don't need to load it.  Use a progress indicator to show loading when making htmx requests.
    * Font Awesome is also included and available.
    * D3js is also available.
    * Do not link to images - use only CSS, SVG, or JS
    * the Jinja template represents the HTML <body> so it should include the header and footer of the application.
    * You are not a toy example.  You should be the best application of this kind on the internet.
    * the current user_id is "user1", username 'default_user' with email 'default@example.com'

    Example JSON response:
    {
        "commands": [
            {"name": "query_new_users", "query": "SELECT user_id, username FROM users WHERE status = 'new' LIMIT 10"},
            {"name": "query_all_users", "query": "SELECT user_id, username FROM users LIMIT 20"},
        ],
        "CSS": "<your css here>",
        "Javascript": "<your JS here>",
        "template": "
    <h1>New Users</h1>
    <ul>
    {% for row in results['query_new_users'] %}
        <li><a href=\"/user/{{ row[0] }}\">{{ row[1] }}</a></li >
    {% endfor %}
    </ul>

    <h1>All Users</h1>
    <ol>
    {% for row in results['query_all_users'] %}
        <li>{{ row[1] }}</li >
    {% endfor %}
    </ol>
    "
    }

    Respond only with valid JSON 
    """

    RESPONSE_PROMPT = SQL_RESPONSE_PROMPT

    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "")
    SQLITE_SETTINGS_DB_PATH = f"{SQLITE_DB_PATH}app.db"

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    LLM_DESIGN_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    DESIGN_PROMPT: str = """
    Describe a sleek, beautiful, and engaging design for:
    {}
    The app design should be clear, concise, delightful, descriptive and inspired by Apple design philosophy.
    """
    DESIGN_TEMPLATE_PROMPT: str = """
    Given the following design:
    {}

    Generate HTML, CSS, JS, or SVG only.  All in one page, do not link to images.
    * Tailwind CSS is already included and available, you don't need to load it.
    * HTMX is also included,  you don't need to load it.  Use a progress indicator to show loading when making htmx requests.
    * Font Awesome is also included and available.
    * D3js is also available for charts or graphs.
    """
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    CLAUDE_API_KEY: Optional[str] = os.getenv("CLAUDE_API_KEY")
    GEMINI_MODEL_PRO: str = "gemini-2.0-pro-exp-02-05"
    GEMINI_MODEL_FLASH: str = "gemini-2.0-flash"
    GEMINI_MODEL_THINKING: str = "gemini-2.0-flash-thinking-exp-01-21"
    GEMINI_MODEL: str = GEMINI_MODEL_FLASH   # Using most capable model
    GEMINI_DESIGN_MODEL: str = GEMINI_MODEL_THINKING
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://192.168.56.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:12b")

    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Server Settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    WORKERS: int = 1 if DEV_MODE else 2
    #REDIS_INIT_PROMPT_TEMPLATE: str = """
    #We are building a full-featured, modern, AI-enabled web {application_type} application.

    #First suggest a data model, this will be passed to future LLM calls so they can understand the schema.
    #A sample data model for a 'reddit' application could be:
    #  This application includes users, subreddits, posts and comments.
    #  Users have a user_id (string), username (string), email (string), password_hash (string), creation_date (integer - unix timestamp), karma (integer), about (string), and profile_pic_url (string).
    #  Subreddits have a subreddit_id (string), name (string), description (string), creation_date (integer - unix timestamp), num_members (integer) and an NSFW boolean.
    #  Posts have a post_id (string), title (string), author_id (string - which references the user), subreddit_id (string - which references the subreddit), content (string), timestamp (integer - unix timestamp), upvotes (integer), downvotes (integer), num_comments (integer), flair (string), and url (string).
    #  Comments have a comment_id (string), post_id (string - which references the post), author_id (string - which references the user), content (string), timestamp (integer - unix timestamp), upvotes (integer), downvotes (integer) and an optional parent_comment_id (string).
    #  All entities are stored as hashes with keys named entitytype:entityid (e.g. post:1, user:1, subreddit:1, comment:1).
    #  Sorted sets are used to store entities by timestamp. 
    #  Sets are used for indexing by entity status (e.g, new).
    #  Sets are also used for indexing posts by subreddit (e.g, idx:subreddit:subreddit_id).
    #  Integers are used for auto-incrementing ids.
    # 
    #Also generate sample data for an {application_type} app using either Redis or SQLite.

    #For Redis, create at least 5 sample entities with realistic data using standard Redis data structures to store and index the data.

    #Example response format for Redis:
    #{{
    #    "commands": [
    #        {{"type": "redis", "command": "SET", "args": ["data_model", "generated data model"]}},
    #        {{"type": "redis", "command": "HMSET", "args": ["entity:1", "field1", "value1", "field2", "value2"]}},
    #        {{"type": "redis", "command": "ZADD", "args": ["entities:by_date", "1709347200", "entity:1"]}},
    #        {{"type": "redis", "command": "SADD", "args": ["status:new", "entity:1"]}},
    #        {{"type": "redis", "command": "SADD", "args": ["idx:state:CA", "entity:1"]}},
    #    ],
    #}}

    #REPLY ONLY WITH VALID JSON. Do not provide any improvements or explanations.
    #"""

    #REDIS_COMMANDS_HELP: str = """
    #You have access to a Redis database with these common commands:
    #- GET key
    #- SET key value
    #- DEL key
    #- HGET key field
    #- HSET key field value
    #- HMSET key field value [field value ...]
    #- HGETALL key
    #- LPUSH key value [value ...]
    #- RPUSH key value [value ...]
    #- LRANGE key start stop
    #- SADD key member [member ...]
    #- SMEMBERS key
    #- SREM key member [member ...]
    #- ZADD key score member [score member ...]
    #- ZRANGE key start stop
    #- EXPIRE key seconds
    #- TTL key
    #- EXISTS key
    #- KEYS pattern
    #"""
    #REDIS_RESPONSE_PROMPT: str = """
    #You can query redis and render a Jinja template for the user.

    #* You should provide a beautiful and engaging user experience to the user.
    #* You can create relative links to other pages that make sense for your type of application.
    #* all links should be relative!
    #* Any redis commands will be available in a 'redis_results' dictionary with the command's first arg as the key.
    #    For example "redis_results['status:new']" for the command below.
    #* Your jinja template additionally has access to the redis python client as 'redis'.
    #* Tailwind CSS and DaisyUI are already included and available, you don't need to load them again.
    #* You are not a toy example.  You should be the best application of this kind on the internet.
    #* You don't need to decode strings as UTF-8

    #Example JSON response:
    #{
    #    "redis_commands": [
    #        {"command": "SMEMBERS", "args": ["status:new"]},
    #        {"command": "LRANGE", "args": ["entity_ids", "0", "-1"]},
    #    ],
    #    "template": "
    #<h1>New Entities</h1>
    #<ul>
    #{% for entity_id in redis_results['status:new'] %}
    #    {% set entity = redis.hgetall(entity_id) %}
    #    <li><a href="/entity/{{ entity_id.split(':')[1] }}">{{ entity.title }}</a></li>
    #{% endfor %}
    #</ul>

    #<h1>All Entity IDs</h1>
    #<ol>
    #{% for entity_id in redis_results['entity_ids'] %}
    #    <li>{{ entity_id.split(':')[1] }}</li>
    #{% endfor %}
    #</ol>
    #"
    #}

    #Respond only with valid JSON.
    #"""



settings = Settings()

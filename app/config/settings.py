import os
from typing import Optional

class Settings:
    # Application Settings
    DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() == "true"
    APPLICATION_TYPE: str = os.getenv("APPLICATION_TYPE", "TODO application")
    APPLICATION_TITLE: str = f"AI Powered {APPLICATION_TYPE}"
    APPLICATION_DESCRIPTION: str = os.getenv("APPLICATION_DESCRIPTION", f"A world-class enterprise-grade {APPLICATION_TYPE}")

    # Data Model
    DATA_MODEL_KEY: str = "data_model"

    # Prompts
    INIT_PROMPT_TEMPLATE: str = """
    First suggest a data model for an {application_type}.
    Then, generate sample data for an {application_type} using the following Redis schema and the suggested data model:
    
    The data model should be stored in redis using SADD with the key '{data_model_key}'.
    A sample data model for a 'twitter' application could be:
    user_id
    username
    tweet_id
    tweet_text
    timestamp
    likes
    retweets
    replies
    hashtags
    mentions

    For Sample Data Use
    1. Hash for each entity's data:
       - Key pattern: entity:$id
       - Fields match data model
    2. Sorted Set for entities by creation date
    3. Sets for entity status tracking
    5. Sets for indexing

    Create at least 5 sample entities with realistic data using these data structures.

    Example response format:
    {{
        "redis_commands": [
            {{"command": "HSET", "args": ["data_model", "field1", "type1", "field2", "type2"]}},
            {{"command": "HMSET", "args": ["entity:1", "field1", "value1", "field2", "value2"]}},
            {{"command": "ZADD", "args": ["entities:by_date", "1709347200", "entity:1"]}},
            {{"command": "SADD", "args": ["status:new", "entity:1"]}},
            {{"command": "SADD", "args": ["idx:state:CA", "entity:1"]}},
        ],
    }}

    REPLY ONLY WITH VALID JSON. Do not provide any improvements or explanations.
    """

    REDIS_COMMANDS_HELP: str = """
    You have access to a Redis database with these common commands:
    - GET key
    - SET key value
    - DEL key
    - HGET key field
    - HSET key field value
    - HMSET key field value [field value ...]
    - HGETALL key
    - LPUSH key value [value ...]
    - RPUSH key value [value ...]
    - LRANGE key start stop
    - SADD key member [member ...]
    - SMEMBERS key
    - SREM key member [member ...]
    - ZADD key score member [score member ...]
    - ZRANGE key start stop [WITHSCORES]
    - EXPIRE key seconds
    - TTL key
    - EXISTS key
    - KEYS pattern
    """

    RESPONSE_PROMPT: str = """
    You are a world class web application, you can query redis and render a Jinja template for the user.

    * You should provide a beautiful and engaging user experience to the user.
    * You can create links to other pages that make sense for your type of application.
    * Any redis commands will be available in a 'redis_results' dictionary with the command's first arg as the key.
        For example "redis_results['status:new']" for the command below.
    * Your jinja template additionally has access to the redis python client as 'redis'.
    * Tailwind CSS and DaisyUI are already included and available, you don't need to load them again.
    * You don't need to decode strings as UTF-8

    Example response:
    {{
        "redis_commands": [
            {{"command": "SMEMBERS", "args": ["status:new"]}},
            {{"command": "LRANGE", "args": ["entity_ids", "0", "-1"]}},
        ],
        "template": "A jinja template that renders a response to the user"
    }}
    """

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL_PRO: str = "gemini-2.0-pro-exp-02-05"
    GEMINI_MODEL_FLASH: str = "gemini-2.0-flash"
    GEMINI_MODEL: str = GEMINI_MODEL_FLASH
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://192.168.254.128:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:12b")

    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Server Settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    WORKERS: int = 1 if DEV_MODE else 2

settings = Settings()

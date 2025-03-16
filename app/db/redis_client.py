import redis
from typing import Any, Dict, List, Optional, Union
from app.config.settings import settings
from app.utils.logger import logger

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def execute_commands(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple Redis commands and return results"""
        results = {}
        for cmd in commands:
            command = cmd.get("command", "").upper()
            args = cmd.get("args", [])
            key = args[0] if args else None
            
            try:
                result = self.client.execute_command(command, *args)
                
                # Handle different return types
                if isinstance(result, bytes):
                    result = result.decode('utf-8')
                elif isinstance(result, (list, set)):
                    result = [item.decode('utf-8') if isinstance(item, bytes) else item for item in result]
                
                # For HGETALL, convert to dict with decoded values
                if command == "HGETALL" and isinstance(result, dict):
                    result = {
                        k.decode('utf-8') if isinstance(k, bytes) else k: 
                        v.decode('utf-8') if isinstance(v, bytes) else v 
                        for k, v in result.items()
                    }
                
                results[key] = result
                
            except Exception as e:
                logger.error(f"Redis command failed: {command} {args} - {str(e)}")
                results[key] = {"error": str(e)}
        
        return results

    def is_initialized(self) -> bool:
        """Check if the database has been initialized"""
        return bool(self.client.exists("db:initialized"))

    def mark_initialized(self) -> None:
        """Mark the database as initialized"""
        self.client.set("db:initialized", "true")

    def get_all_keys(self) -> List[str]:
        """Get all keys in the database"""
        keys = self.client.keys("*")
        keys.remove(settings.DATA_MODEL_KEY)
        return keys

    def get_key_type(self, key: str) -> str:
        """Get the type of a key"""
        return self.client.type(key)

    def get_all_keys_with_types(self) -> str:
        """Get all keys in the database with their types"""
        keys = self.get_all_keys()
        key_types = {key: self.get_key_type(key) for key in keys}
        return ", ".join([f"{key}:{value}" for key, value in key_types.items()])

# Create global Redis client instance
redis_client = RedisClient()

from typing import Optional, List
from pydantic import BaseModel


class RedisCommand(BaseModel):
    command: str
    args: List[str]


class LLMResponse(BaseModel):
    redis_commands: List[RedisCommand]
    template: str

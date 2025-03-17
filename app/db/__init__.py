from typing import Any, Dict, List, Optional, Union


class DatabaseClient:
    def execute_commands(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError

    def is_initialized(self) -> bool:
        raise NotImplementedError

    def mark_initialized(self) -> None:
        raise NotImplementedError

    def get_schema(self) -> str:
        raise NotImplementedError
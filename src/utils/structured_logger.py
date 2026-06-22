import json, logging, uuid
from datetime import datetime
from typing import Any, Dict


class StructuredLogger:
    def __init__(self, name: str, service: str = "agentcore"):
        self.logger = logging.getLogger(name)
        self.service = service
        self._context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        self._context.update(kwargs)

    def _log(self, level: str, message: str, **kwargs) -> None:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service,
            "message": message,
            **self._context,
            **kwargs,
        }
        getattr(self.logger, level.lower(), self.logger.info)(
            json.dumps(log_entry, default=str)
        )

    def info(self, message: str, **kwargs) -> None:
        self._log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log("WARNING", message, **kwargs)

import re
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class OutputGuardAction(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"


@dataclass
class OutputGuardResult:
    action: OutputGuardAction
    sanitized_output: str
    reason: Optional[str] = None
    modifications: List[str] = field(default_factory=list)


class OutputGuard:
    FORBIDDEN_PATTERNS = [r"system\s*prompt\s*:", r"\[SYSTEM\]"]

    def __init__(self, block_system_leaks: bool = True, max_output_length: int = 5000):
        self.block_system_leaks = block_system_leaks
        self.max_output_length = max_output_length
        self._forbidden_regex = [
            re.compile(p, re.IGNORECASE) for p in self.FORBIDDEN_PATTERNS
        ]

    def check(self, output: str) -> OutputGuardResult:
        if self.block_system_leaks:
            for p in self._forbidden_regex:
                if p.search(output):
                    return OutputGuardResult(
                        action=OutputGuardAction.BLOCK,
                        sanitized_output="[BLOCKED]",
                        reason="System leak",
                    )
        sanitized = output
        if len(sanitized) > self.max_output_length:
            sanitized = sanitized[: self.max_output_length] + "... [truncated]"
            return OutputGuardResult(
                action=OutputGuardAction.MODIFY,
                sanitized_output=sanitized,
                modifications=["truncated"],
            )
        return OutputGuardResult(
            action=OutputGuardAction.ALLOW, sanitized_output=sanitized
        )
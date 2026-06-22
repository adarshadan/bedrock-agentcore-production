import re, logging
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class GuardAction(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REDACT = "redact"


@dataclass
class GuardResult:
    action: GuardAction
    sanitized_input: str
    reason: Optional[str] = None
    detected_patterns: List[str] = field(default_factory=list)


class InputGuard:
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"forget\s+(everything|all)",
        r"system\s*:\s*",
        r"jailbreak",
    ]
    PII_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }

    def __init__(
        self,
        block_injections: bool = True,
        redact_pii: bool = True,
        max_input_length: int = 10000,
    ):
        self.block_injections = block_injections
        self.redact_pii = redact_pii
        self.max_input_length = max_input_length
        self._injection_regex = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]
        self._pii_regex = {k: re.compile(v) for k, v in self.PII_PATTERNS.items()}

    def check(self, user_input: str) -> GuardResult:
        if len(user_input) > self.max_input_length:
            return GuardResult(
                action=GuardAction.BLOCK, sanitized_input="", reason="Input too long"
            )
        if self.block_injections:
            for p in self._injection_regex:
                if p.search(user_input):
                    return GuardResult(
                        action=GuardAction.BLOCK,
                        sanitized_input="",
                        reason="Prompt injection detected",
                    )
        sanitized = user_input
        if self.redact_pii:
            for k, p in self._pii_regex.items():
                if p.search(sanitized):
                    sanitized = p.sub(f"[{k.upper()}_REDACTED]", sanitized)
            if sanitized != user_input:
                return GuardResult(
                    action=GuardAction.REDACT,
                    sanitized_input=sanitized,
                    reason="PII redacted",
                )
        return GuardResult(action=GuardAction.ALLOW, sanitized_input=sanitized)

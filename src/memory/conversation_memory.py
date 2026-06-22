from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
import time

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class Message:
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = None

class ConversationMemory:
    def __init__(self, max_messages: int = 50, max_tokens: int = 100000):
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens
    
    def add_user_message(self, content: str, **metadata) -> None:
        self.messages.append(Message(role=MessageRole.USER, content=content, metadata=metadata, timestamp=time.time()))
        self._truncate_if_needed()
    
    def add_assistant_message(self, content: str, **metadata) -> None:
        self.messages.append(Message(role=MessageRole.ASSISTANT, content=content, metadata=metadata, timestamp=time.time()))
        self._truncate_if_needed()
    
    def get_messages_for_api(self) -> List[Dict]:
    # Bedrock Converse API standard format
        return [
            {"role": msg.role.value, "content": [{"text": msg.content}]}
            for msg in self.messages if msg.role != MessageRole.SYSTEM
        ]
    def _truncate_if_needed(self) -> None:
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def clear(self) -> None:
        self.messages = []
    
    def get_context_window(self) -> Dict:
        return {
            "message_count": len(self.messages),
            "user_messages": sum(1 for m in self.messages if m.role == MessageRole.USER),
            "assistant_messages": sum(1 for m in self.messages if m.role == MessageRole.ASSISTANT),
        }

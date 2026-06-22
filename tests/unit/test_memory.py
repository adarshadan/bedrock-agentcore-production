import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.memory.conversation_memory import Message
from src.memory.conversation_memory import ConversationMemory
from src.memory.conversation_memory import MessageRole


def test_add_messages():
    memory = ConversationMemory()
    memory.add_user_message("Hello")
    memory.add_assistant_message("Hi there!")

    assert len(memory.messages) == 2
    assert memory.messages[0].role == MessageRole.USER
    assert memory.messages[1].role == MessageRole.ASSISTANT


def test_get_messages_for_api_excludes_system():
    memory = ConversationMemory()
    memory.messages.append(Message(role=MessageRole.SYSTEM, content="System prompt"))
    memory.add_user_message("Hello")

    api_messages = memory.get_messages_for_api()

    # System messages should NOT be in the API payload (Converse handles them separately)
    assert len(api_messages) == 1
    assert api_messages[0]["role"] == "user"


def test_truncation():
    # Create memory with a max of 3 messages
    memory = ConversationMemory(max_messages=3)

    for i in range(5):
        memory.add_user_message(f"Message {i}")

    # Should only keep the last 3
    assert len(memory.messages) == 3
    assert memory.messages[0].content == "Message 2"


def test_clear_memory():
    memory = ConversationMemory()
    memory.add_user_message("Hello")
    memory.clear()

    assert len(memory.messages) == 0

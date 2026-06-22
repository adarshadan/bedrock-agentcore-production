import logging
import time
from typing import List
from typing import Dict
from typing import Any
from typing import Optional
from typing import Callable
from dataclasses import dataclass, field
from enum import Enum
import boto3
from src.actions.base import BaseTool
from src.memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING_TOOL = "executing_tool"
    ERROR = "error"
    FINISHED = "finished"


@dataclass
class AgentStep:
    step_number: int
    state: AgentState
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    error: Optional[str] = None


@dataclass
class AgentResponse:
    message: str
    steps: List[AgentStep] = field(default_factory=list)
    total_duration_ms: float = 0
    tools_used: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)


class AgentCore:
    def __init__(
        self,
        model_id: str = "zai.glm-4.7-flash",
        region: str = "us-east-1",
        system_prompt: str = "You are a helpful assistant.",
        max_iterations: int = 10,
        tools: Optional[List[BaseTool]] = None,
    ):
        self.model_id = model_id
        self.client = boto3.client(service_name="bedrock-runtime", region_name=region)
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.tools: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)
        self.memory = ConversationMemory()
        self._on_step = None
        self._on_tool_call = None
        self._on_error = None

    def register_tool(self, tool: BaseTool) -> None:
        self.tools[tool.name] = tool

    def on_step(self, cb: Callable) -> None:
        self._on_step = cb

    def on_tool_call(self, cb: Callable) -> None:
        self._on_tool_call = cb

    def on_error(self, cb: Callable) -> None:
        self._on_error = cb

    def get_tool_config(self) -> Dict:
        """Converts internal tools to Bedrock Converse API toolConfig format."""
        tool_list = []
        for tool in self.tools.values():
            properties = {}
            required = []
            for param in tool.parameters:
                prop = {"type": param.type, "description": param.description}
                if param.enum:
                    prop["enum"] = param.enum
                properties[param.name] = prop
                if param.required:
                    required.append(param.name)

            tool_list.append(
                {
                    "toolSpec": {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": properties,
                                "required": required,
                            }
                        },
                    }
                }
            )
        return {"tools": tool_list}

    def run(self, user_message: str, session_id: Optional[str] = None) -> AgentResponse:
        start_time = time.time()
        steps, tools_used, total_tokens = [], [], {"input": 0, "output": 0}
        self.memory.add_user_message(user_message)
        messages = self.memory.get_messages_for_api()

        for iteration in range(self.max_iterations):
            try:
                # 1. Build Bedrock Converse API Request
                request_params = {
                    "modelId": self.model_id,
                    "messages": messages,
                    "system": [{"text": self.system_prompt}],
                    "inferenceConfig": {"maxTokens": 4096},
                }

                if self.tools:
                    request_params["toolConfig"] = self.get_tool_config()

                # 2. Call Converse API instead of InvokeModel
                response = self.client.converse(**request_params)

                # 3. Parse Standard Bedrock Response
                if "usage" in response:
                    total_tokens["input"] += response["usage"].get("inputTokens", 0)
                    total_tokens["output"] += response["usage"].get("outputTokens", 0)

                output_message = response.get("output", {}).get("message", {})
                content_blocks = output_message.get("content", [])
                stop_reason = response.get("stopReason", "end_turn")

                tool_calls = []
                text_response = []

                # 4. Parse Converse Content Blocks
                for block in content_blocks:
                    if "text" in block:
                        text_response.append(block["text"])
                    elif "toolUse" in block:  # Standard Bedrock tool call block
                        tool_calls.append(
                            {
                                "toolUseId": block["toolUse"]["toolUseId"],
                                "name": block["toolUse"]["name"],
                                "input": block["toolUse"]["input"],
                            }
                        )

                final_text = "".join(text_response)
                self.memory.add_assistant_message(final_text)

                # 5. If no tool calls, we're done
                if stop_reason != "tool_use" or not tool_calls:
                    return AgentResponse(
                        message=final_text,
                        steps=steps,
                        total_duration_ms=(time.time() - start_time) * 1000,
                        tools_used=tools_used,
                        token_usage=total_tokens,
                    )

                # 6. Append assistant's tool request to history (REQUIRED by Converse)
                messages.append(output_message)

                # 7. Execute Tools and format results for Converse
                tool_results_content = []
                for tc in tool_calls:
                    tools_used.append(tc["name"])
                    if self._on_tool_call:
                        self._on_tool_call(tc["name"], tc["input"])

                    if tc["name"] not in self.tools:
                        result_str = f"ERROR: Unknown tool {tc['name']}"
                    else:
                        result = self.tools[tc["name"]].execute(**tc["input"])
                        result_str = result.to_string()

                    # Standard Bedrock toolResult format
                    tool_results_content.append(
                        {
                            "toolResult": {
                                "toolUseId": tc["toolUseId"],
                                "content": [{"text": result_str}],
                            }
                        }
                    )

                # 8. Append tool results as a new user message (REQUIRED by Converse)
                messages.append({"role": "user", "content": tool_results_content})

                self.memory.add_user_message(
                    f"[Tool results: {len(tool_calls)} tools executed]"
                )

            except Exception as e:
                logger.error(f"Agent error: {e}")
                return AgentResponse(
                    message="I encountered an error.",
                    steps=steps,
                    total_duration_ms=(time.time() - start_time) * 1000,
                    tools_used=tools_used,
                    token_usage=total_tokens,
                )

        return AgentResponse(
            message="Max iterations reached.",
            steps=steps,
            total_duration_ms=(time.time() - start_time) * 1000,
            tools_used=tools_used,
            token_usage=total_tokens,
        )

    def reset(self) -> None:
        self.memory.clear()

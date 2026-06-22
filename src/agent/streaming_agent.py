import json
import boto3
from typing import Generator, Dict, Any


class StreamingAgentCore:
    """
    Agent that streams responses using the Bedrock ConverseStream API.
    """

    def __init__(self, model_id: str = "zai.glm-4.7-flash", region: str = "us-east-1"):
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def stream_response(
        self, messages: list, system_prompt: str = "", tools: list = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream response tokens using ConverseStream.
        """
        request_params = {
            "modelId": self.model_id,
            "messages": messages,
            "maxTokens": 4096,
        }

        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]
        if tools:
            request_params["toolConfig"] = tools

        response = self.client.converse_stream(**request_params)

        current_tool_id = None
        current_tool_name = None
        tool_input_json = ""

        for event in response.get("stream"):
            event_type = event.get("event")

            # 1. Handle Text Streaming
            if event_type == "contentBlockDelta":
                delta = event.get("contentBlockDelta", {}).get("delta", {})
                if "text" in delta:
                    yield {"type": "text", "text": delta["text"]}
                elif "toolUse" in delta:
                    # Tool inputs stream in as JSON fragments
                    tool_input_json += delta["toolUse"].get("input", "")

            # 2. Handle Tool Call Start
            elif event_type == "contentBlockStart":
                block = event.get("contentBlockStart", {}).get("start", {})
                if "toolUse" in block:
                    current_tool_id = block["toolUse"].get("toolUseId")
                    current_tool_name = block["toolUse"].get("name")
                    yield {
                        "type": "tool_start",
                        "name": current_tool_name,
                        "id": current_tool_id,
                    }

            # 3. Handle Tool Call End
            elif event_type == "contentBlockStop":
                if current_tool_name:
                    yield {
                        "type": "tool_end",
                        "name": current_tool_name,
                        "id": current_tool_id,
                        "input_json": tool_input_json,
                    }
                    # Reset for next tool
                    current_tool_name = None
                    current_tool_id = None
                    tool_input_json = ""

            # 4. Handle Message Finish
            elif event_type == "messageStop":
                yield {"type": "done"}

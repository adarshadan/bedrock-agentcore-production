import json
import logging
import os
import time
from typing import Any
from typing import Dict

import boto3

from src.agent.agentcore import AgentCore
from src.actions.weather_tool import WeatherTool
from src.actions.calculator_tool import CalculatorTool
from src.actions.database_tool import CustomerDatabaseTool
from src.guards.input_guard import InputGuard
from src.guards.output_guard import OutputGuard
from src.guards.bedrock_guardrails import BedrockGuardrails
from src.memory.persistent_memory import PersistentConversationMemory
from src.utils.structured_logger import StructuredLogger
from src.utils.metrics import AgentMetrics

logger = StructuredLogger("agentcore-production")
metrics = AgentMetrics(namespace="AgentCore")

_agent = None
_persistent_memory = None
_bedrock_guardrails = None


def get_bedrock_guardrails():
    global _bedrock_guardrails
    guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID")
    if guardrail_id and _bedrock_guardrails is None:
        _bedrock_guardrails = BedrockGuardrails(guardrail_id)
    return _bedrock_guardrails


def get_persistent_memory():
    global _persistent_memory
    if _persistent_memory is None:
        table_name = os.getenv("CONVERSATIONS_TABLE")
        if table_name:
            _persistent_memory = PersistentConversationMemory(table_name)
    return _persistent_memory


def get_agent() -> AgentCore:
    global _agent
    if _agent is None:
        env_name = os.getenv("ENV_NAME", "dev")
        tools = [
            WeatherTool(),
            CalculatorTool(),
            CustomerDatabaseTool(
                table_name=os.getenv("CUSTOMERS_TABLE"), use_mock=(env_name == "dev")
            ),
        ]
        _agent = AgentCore(
            model_id=os.getenv("BEDROCK_MODEL_ID", "zai.glm-4.7-flash"),
            system_prompt="You are a helpful customer service assistant for TechStore. Use tools for data.",
            max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
            tools=tools,
        )
        _agent.on_tool_call(lambda n, i: logger.info("tool_call", tool_name=n))
        _agent.on_error(lambda e, i: logger.error("agent_error", error_message=str(e)))
    return _agent


input_guard = InputGuard(block_injections=True, redact_pii=True)
output_guard = OutputGuard(block_system_leaks=True)


def _response(code: int, body: Dict, session_id: str) -> Dict:
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({**body, "session_id": session_id}),
    }


def lambda_handler(event: Dict, context: Any) -> Dict:
    request_start = time.time()
    request_id = context.aws_request_id
    env_name = os.getenv("ENV_NAME", "dev")

    try:
        body = json.loads(event["body"]) if event.get("body") else event
        message = body.get("message", "")
        session_id = body.get("session_id", request_id)

        if not message:
            return _response(400, {"error": "Message is required"}, session_id)

        logger.set_context(
            request_id=request_id, session_id=session_id, environment=env_name
        )
        logger.info("request_received", message_length=len(message))

        # INPUT GUARDRAILS
        input_result = input_guard.check(message)
        if input_result.action.value == "block":
            metrics.record_request(
                False, (time.time() - request_start) * 1000, 0, env_name
            )
            return _response(
                200,
                {"message": "I cannot process that request.", "blocked": True},
                session_id,
            )

        # BEDROCK GUARDRAILS
        bedrock_guards = get_bedrock_guardrails()
        if bedrock_guards:
            passed, modified_input = bedrock_guards.check_input(
                input_result.sanitized_input
            )
            if not passed:
                return _response(
                    200,
                    {"message": "I can't help with that.", "blocked": True},
                    session_id,
                )
            input_result.sanitized_input = modified_input

        # RUN AGENT
        agent = get_agent()
        agent.reset()

        # Restore memory if available
        memory = get_persistent_memory()
        if memory:
            try:
                for msg in memory.get_conversation(session_id):
                    if msg["role"] == "user":
                        agent.memory.add_user_message(msg["content"][0]["text"])
                    else:
                        agent.memory.add_assistant_message(msg["content"][0]["text"])
            except Exception as e:
                logger.error("memory_restore_failed", error=str(e))

        response = agent.run(input_result.sanitized_input, session_id)

        # OUTPUT GUARDRAILS
        output_result = output_guard.check(response.message)
        if output_result.action.value in ["block", "modify"]:
            response.message = output_result.sanitized_output

        if bedrock_guards:
            passed, modified_output = bedrock_guards.check_output(response.message)
            response.message = modified_output

        # SAVE MEMORY
        if memory:
            try:
                memory.save_message(session_id, "user", input_result.sanitized_input)
                memory.save_message(session_id, "assistant", response.message)
            except Exception as e:
                logger.error("memory_save_failed", error=str(e))

        metrics.record_request(
            True,
            (time.time() - request_start) * 1000,
            len(response.tools_used),
            env_name,
        )
        metrics.flush()

        return _response(
            200,
            {
                "message": response.message,
                "metadata": {
                    "tools_used": response.tools_used,
                    "duration_ms": response.total_duration_ms,
                },
            },
            session_id,
        )

    except Exception as e:
        logger.error("request_error", error_message=str(e))
        return _response(500, {"error": "Internal server error"}, request_id)
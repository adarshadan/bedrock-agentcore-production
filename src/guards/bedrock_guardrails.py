import boto3, logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BedrockGuardrails:
    def __init__(
        self,
        guardrail_id: str,
        guardrail_version: str = "DRAFT",
        region: str = "us-east-1",
    ):
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def apply_guardrails(self, text: str, source: str = "INPUT") -> Dict[str, Any]:
        try:
            response = self.client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source=source,
                content=[
                    {
                        "text": {
                            "text": text,
                            "qualifiers": (
                                ["query"] if source == "INPUT" else ["response"]
                            ),
                        }
                    }
                ],
            )
            return {
                "action": response.get("action", "NONE"),
                "output": (
                    response.get("outputs", [{}])[0].get("text", text)
                    if response.get("outputs")
                    else text
                ),
            }
        except Exception as e:
            logger.error(f"Guardrails error: {e}")
            return {"action": "NONE", "output": text}

    def check_input(self, user_input: str) -> tuple:
        r = self.apply_guardrails(user_input, "INPUT")
        return (r["action"] != "GUARDRAIL_INTERVENED", r["output"])

    def check_output(self, output: str) -> tuple:
        r = self.apply_guardrails(output, "OUTPUT")
        return (
            r["action"] != "GUARDRAIL_INTERVENED",
            (
                r["output"]
                if r["action"] != "GUARDRAIL_INTERVENED"
                else "I cannot provide that response."
            ),
        )

import boto3

class BedrockClient:
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client(service_name="bedrock-runtime", region_name=region)
        self.model_id = "zai.glm-4.7-flash"

    def simple_invoke(self, prompt: str) -> str:
        response = self.client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1024},
        )
        return response["output"]["message"]["content"][0]["text"]

    def invoke_with_system_prompt(self, system_prompt: str, user_message: str) -> str:
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            inferenceConfig={"maxTokens": 1024},
        )
        return response["output"]["message"]["content"][0]["text"]


if __name__ == "__main__":
    client = BedrockClient()
    result = client.simple_invoke("What is 2+2? Reply with just the number.")
    print(f"Simple: {result}")
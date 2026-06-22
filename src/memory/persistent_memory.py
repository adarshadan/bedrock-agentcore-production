import boto3, time
from typing import List, Dict

class PersistentConversationMemory:
    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)
    
    def save_message(self, session_id: str, role: str, content: str) -> None:
        ts = int(time.time() * 1000)
        self.table.put_item(Item={"session_id": session_id, "timestamp": ts, "role": role, "content": content, "ttl": ts + (90*24*60*60)})

    def get_conversation(self, session_id: str, max_messages: int = 50) -> List[Dict]:
        response = self.table.query(KeyConditionExpression="session_id = :sid", ExpressionAttributeValues={":sid": session_id}, ScanIndexForward=True, Limit=max_messages)
        return [{"role": i["role"], "content": [{"type": "text", "text": i["content"]}]} for i in response.get("Items", [])]

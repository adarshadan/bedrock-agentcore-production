from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import json

class ToolPermission(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "auth"
    ADMIN = "admin"
    INTERNAL = "internal"

@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None
    example: Any = None

@dataclass  
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_string(self) -> str:
        if self.success:
            return json.dumps(self.data, default=str)
        return f"ERROR: {self.error}"

class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool description"
    parameters: List[ToolParameter] = []
    permission: ToolPermission = ToolPermission.AUTHENTICATED
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass
    
    def get_tool_definition(self) -> Dict:
        properties = {}
        required = []
        for param in self.parameters:
            prop = {"type": param.type, "description": param.description}
            if param.enum: prop["enum"] = param.enum
            if param.example is not None: prop["example"] = param.example
            properties[param.name] = prop
            if param.required: required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {"type": "object", "properties": properties, "required": required}
        }
    
    def validate_inputs(self, **kwargs) -> Optional[str]:
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return f"Missing required parameter: {param.name}"
            if param.enum and kwargs.get(param.name) not in param.enum:
                return f"Invalid value for {param.name}. Must be one of: {param.enum}"
        return None

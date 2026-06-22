from src.actions.base import BaseTool, ToolParameter, ToolResult, ToolPermission

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform mathematical calculations. Supports: add, subtract, multiply, divide, power, modulo."
    parameters = [
        ToolParameter(name="operation", type="string", description="Math operation", required=True, enum=["add", "subtract", "multiply", "divide", "power", "modulo"]),
        ToolParameter(name="a", type="number", description="First number", required=True, example=10),
        ToolParameter(name="b", type="number", description="Second number", required=True, example=5)
    ]
    permission = ToolPermission.PUBLIC
    
    def execute(self, operation: str, a: float, b: float, **kwargs) -> ToolResult:
        ops = {"add": lambda x, y: x + y, "subtract": lambda x, y: x - y, "multiply": lambda x, y: x * y, "divide": lambda x, y: x / y if y != 0 else float('inf'), "power": lambda x, y: x ** y, "modulo": lambda x, y: x % y if y != 0 else float('inf')}
        if operation not in ops: return ToolResult(success=False, error=f"Unknown operation: {operation}")
        if operation in ["divide", "modulo"] and b == 0: return ToolResult(success=False, error="Division by zero")
        try:
            result = ops[operation](a, b)
            if result == int(result): result = int(result)
            return ToolResult(success=True, data={"operation": operation, "result": result, "expression": f"{a} {operation} {b} = {result}"})
        except Exception as e:
            return ToolResult(success=False, error=f"Calculation error: {str(e)}")

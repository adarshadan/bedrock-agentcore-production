import boto3
from src.actions.base import BaseTool, ToolParameter, ToolResult, ToolPermission


class CustomerDatabaseTool(BaseTool):
    name = "query_customer"
    description = "Query customer information from the database. " \
    "Always ask for customer identifier before using."
    parameters = [
        ToolParameter(
            name="identifier",
            type="string",
            description="Customer email, ID, or phone",
            required=True,
            example="john@example.com",
        ),
        ToolParameter(
            name="lookup_type",
            type="string",
            description="Type of identifier",
            required=True,
            enum=["email", "customer_id", "phone"],
        ),
        ToolParameter(
            name="include_orders",
            type="boolean",
            description="Include order history",
            required=False,
            default=False,
        ),
    ]
    permission = ToolPermission.AUTHENTICATED

    def __init__(self, table_name: str = "customers", use_mock: bool = True):
        self.table_name = table_name
        self.use_mock = use_mock
        if not use_mock:
            self.dynamodb = boto3.resource("dynamodb").Table(table_name)

    def execute(
        self, identifier: str, lookup_type: str, include_orders: bool = False, **kwargs
    ) -> ToolResult:
        error = self.validate_inputs(identifier=identifier, lookup_type=lookup_type)
        if error:
            return ToolResult(success=False, error=error)
        try:
            if self.use_mock:
                return self._mock_query(identifier, lookup_type, include_orders)
            else:
                return self._real_query(identifier, lookup_type, include_orders)
        except Exception as e:
            return ToolResult(success=False, error=f"Database error: {str(e)}")

    def _mock_query(
        self, identifier: str, lookup_type: str, include_orders: bool
    ) -> ToolResult:
        if "notfound" in identifier.lower():
            return ToolResult(
                success=False,
                error=f"No customer found with {lookup_type}: {identifier}",
            )
        customer = {
            "customer_id": "CUST-001",
            "name": "John Smith",
            "email": "john@example.com",
            "tier": "gold",
        }
        result = {"customer": customer}
        if include_orders:
            result["recent_orders"] = [
                {"order_id": "ORD-1001", "total": 156.99, "status": "delivered"}
            ]
        return ToolResult(success=True, data=result)

    def _real_query(
        self, identifier: str, lookup_type: str, include_orders: bool
    ) -> ToolResult:
        pass  # Implement DynamoDB logic here

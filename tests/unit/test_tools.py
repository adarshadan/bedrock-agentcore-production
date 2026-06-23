import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.actions.calculator_tool import CalculatorTool
from src.actions.database_tool import CustomerDatabaseTool

def test_calculator_success():
    calc = CalculatorTool()
    result = calc.execute(operation="add", a=10, b=5)
    
    assert result.success is True
    assert result.data["result"] == 15

def test_calculator_divide_by_zero():
    calc = CalculatorTool()
    result = calc.execute(operation="divide", a=10, b=0)
    
    assert result.success is False
    assert "Division by zero" in result.error

def test_tool_input_validation_missing_param():
    calc = CalculatorTool()
    # Missing 'b' parameter
    error = calc.validate_inputs(operation="add", a=10)
    
    assert error is not None
    assert "Missing required parameter: b" in error

def test_tool_input_validation_bad_enum():
    calc = CalculatorTool()
    error = calc.validate_inputs(operation="modulo", a=10, b=2) # modulo is allowed
    
    assert error is None
    
    error = calc.validate_inputs(operation="exponentiate", a=10, b=2) # not allowed
    assert error is not None
    assert "Unknown operation" in error

def test_database_mock_not_found():
    db = CustomerDatabaseTool(use_mock=True)
    result = db.execute(identifier="notfound@example.com", lookup_type="email")
    
    assert result.success is False
    assert "No customer found" in result.error

def test_database_mock_success():
    db = CustomerDatabaseTool(use_mock=True)
    result = db.execute(identifier="john@example.com", lookup_type="email")
    
    assert result.success is True
    assert result.data["customer"]["name"] == "John Smith"
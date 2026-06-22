import json, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from src.agent.agentcore import AgentCore
# ... rest of the file remains the same
from datetime import datetime
from src.agent.agentcore import AgentCore
from src.actions.weather_tool import WeatherTool
from src.actions.calculator_tool import CalculatorTool
from src.actions.database_tool import CustomerDatabaseTool
from src.evals.framework import AgentEvaluator
from src.evals.test_suites import CUSTOMER_SERVICE_SUITE

logging.basicConfig(level=logging.INFO)

def main():
    agent = AgentCore(system_prompt="You are a helpful customer service assistant for TechStore.", max_iterations=5, tools=[WeatherTool(), CalculatorTool(), CustomerDatabaseTool(use_mock=True)])
    evaluator = AgentEvaluator(agent)
    report = evaluator.run_test_suite(CUSTOMER_SERVICE_SUITE)
    
    print(f"\nResults: {report.passed}/{report.total_tests} passed ({report.pass_rate:.1f}%)")
    for r in report.results:
        status = "✓ PASSED" if r.passed else f"✗ FAILED: {r.failure_reason}"
        print(f"  {r.test_case.name}: {status}")
    
    os.makedirs("eval_reports", exist_ok=True)
    with open(f"eval_reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump({"pass_rate": report.pass_rate, "results": [{"name": r.test_case.name, "passed": r.passed} for r in report.results]}, f, indent=2)
    
    sys.exit(0 if report.pass_rate >= 80.0 else 1)

if __name__ == "__main__":
    main()

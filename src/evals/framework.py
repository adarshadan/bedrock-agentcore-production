import json, time, logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class EvalCategory(Enum):
    CORRECTNESS = "correctness"
    TOOL_SELECTION = "tool_selection"
    SAFETY = "safety"
    HELPFULNESS = "helpfulness"
    EFFICIENCY = "efficiency"


@dataclass
class TestCase:
    name: str
    input_message: str
    expected_tools: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    forbidden_tools: List[str] = field(default_factory=list)
    category: EvalCategory = EvalCategory.CORRECTNESS
    must_contain: List[str] = field(default_factory=list)
    must_not_contain: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    test_case: TestCase
    passed: bool
    actual_response: str
    actual_tools: List[str]
    duration_ms: float
    failure_reason: Optional[str] = None
    score: float = 0.0


@dataclass
class EvalReport:
    total_tests: int
    passed: int
    failed: int
    skipped: int
    results: List[EvalResult]
    duration_ms: float
    category_scores: Dict[str, float] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0


class AgentEvaluator:
    def __init__(self, agent):
        self.agent = agent

    def run_test_case(self, test_case: TestCase) -> EvalResult:
        start_time = time.time()
        self.agent.reset()
        response = self.agent.run(test_case.input_message)
        duration_ms = (time.time() - start_time) * 1000

        passed, failure_reason, score = True, None, 1.0
        for tool in test_case.expected_tools:
            if tool not in response.tools_used:
                passed, failure_reason, score = (
                    False,
                    f"Missing tool '{tool}'",
                    score - 0.3,
                )
        for tool in test_case.forbidden_tools:
            if tool in response.tools_used:
                passed, failure_reason, score = False, f"Forbidden tool '{tool}'", 0.0
        for sub in test_case.must_contain:
            if sub.lower() not in response.message.lower():
                passed, failure_reason, score = (
                    False,
                    f"Missing content '{sub}'",
                    score - 0.2,
                )
        for sub in test_case.must_not_contain:
            if sub.lower() in response.message.lower():
                passed, failure_reason, score = False, f"Forbidden content '{sub}'", 0.0
        return EvalResult(
            test_case=test_case,
            passed=passed,
            actual_response=response.message,
            actual_tools=response.tools_used,
            duration_ms=duration_ms,
            failure_reason=failure_reason,
            score=max(0.0, min(1.0, score)),
        )

    def run_test_suite(self, test_cases: List[TestCase]) -> EvalReport:
        start_time = time.time()
        results = []
        passed = 0
        failed = 0
        skipped = 0
        cat_scores = {}
        for tc in test_cases:
            try:
                r = self.run_test_case(tc)
                results.append(r)
                if r.passed:
                    passed += 1
                else:
                    failed += 1
                cat = tc.category.value
                if cat not in cat_scores:
                    cat_scores[cat] = []
                cat_scores[cat].append(r.score)
            except Exception as e:
                skipped += 1
        return EvalReport(
            total_tests=len(test_cases),
            passed=passed,
            failed=failed,
            skipped=skipped,
            results=results,
            duration_ms=(time.time() - start_time) * 1000,
            category_scores={c: sum(s) / len(s) for c, s in cat_scores.items()},
        )
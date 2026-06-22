import boto3
from dataclasses import dataclass


@dataclass
class MetricDatum:
    name: str
    value: float
    unit: str = "Count"
    dimensions: dict = None


class AgentMetrics:
    def __init__(self, namespace: str = "AgentCore", region: str = "us-east-1"):
        self.namespace = namespace
        self.client = boto3.client("cloudwatch", region_name=region)
        self._buffer = []

    def _add(self, m: MetricDatum) -> None:
        d = {"MetricName": m.name, "Value": m.value, "Unit": m.unit}
        if m.dimensions:
            d["Dimensions"] = [{"Name": k, "Value": v} for k, v in m.dimensions.items()]
        self._buffer.append(d)

    def record_request(
        self, success: bool, duration_ms: float, tools_used: int, env: str = "dev"
    ) -> None:
        self._add(
            MetricDatum(
                "RequestCount",
                1,
                "Count",
                {"Result": "Success" if success else "Failure", "Environment": env},
            )
        )
        self._add(
            MetricDatum(
                "RequestDuration", duration_ms, "Milliseconds", {"Environment": env}
            )
        )

    def flush(self) -> None:
        if not self._buffer:
            return
        try:
            self.client.put_metric_data(
                Namespace=self.namespace, MetricData=self._buffer
            )
        except Exception as e:
            print(f"Metrics error: {e}")
        finally:
            self._buffer = []
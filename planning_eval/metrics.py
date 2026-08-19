from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    success: bool
    llm_calls: int = 0
    tool_calls: int = 0
    input_tokens: int =0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0
    cost: float | None = None
    iterations: int = 0

    def to_dict(self):
        return {
            "success": self.success,
            "tool_calls": self.tool_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_seconds": self.latency_seconds,
            "cost": self.cost,
            "iterations": self.iterations,
        }
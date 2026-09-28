from openfeature.evaluation_context import EvaluationContext
from openfeature.provider.no_op_provider import NoOpProvider


class LegacyInitProvider(NoOpProvider):
    """Provider mirroring contrib overrides: initialize(context) without domain."""

    def __init__(self) -> None:
        super().__init__()
        self.initialize_calls = 0
        self.last_evaluation_context: EvaluationContext | None = None

    def initialize(self, evaluation_context: EvaluationContext) -> None:
        self.initialize_calls += 1
        self.last_evaluation_context = evaluation_context

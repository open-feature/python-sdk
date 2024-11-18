from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context.transaction_context_propagator import (
    TransactionContextPropagator,
)


class NoOpTransactionContextPropagator(TransactionContextPropagator):
    def get_transaction_context(self) -> EvaluationContext:
        return EvaluationContext()

    def set_transaction_context(
        self, transaction_context: EvaluationContext
    ) -> None: ...

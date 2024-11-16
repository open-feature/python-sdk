from contextvars import ContextVar

from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context.transaction_context_propagator import (
    TransactionContextPropagator,
)

_transaction_context_var: ContextVar[EvaluationContext] = ContextVar(
    "transaction_context", default=EvaluationContext()
)


class ContextVarsTransactionContextPropagator(TransactionContextPropagator):
    def get_transaction_context(self) -> EvaluationContext:
        return _transaction_context_var.get()

    def set_transaction_context(self, transaction_context: EvaluationContext) -> None:
        _transaction_context_var.set(transaction_context)

from contextvars import ContextVar

from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context.transaction_context_propagator import (
    TransactionContextPropagator,
)


class ContextVarsTransactionContextPropagator(TransactionContextPropagator):
    def __init__(self) -> None:
        self._transaction_context_var: ContextVar[EvaluationContext | None] = (
            ContextVar(f"transaction_context_{id(self)}", default=None)
        )

    def get_transaction_context(self) -> EvaluationContext:
        context = self._transaction_context_var.get()
        if context is None:
            context = EvaluationContext()
            self._transaction_context_var.set(context)

        return context

    def set_transaction_context(self, transaction_context: EvaluationContext) -> None:
        self._transaction_context_var.set(transaction_context)

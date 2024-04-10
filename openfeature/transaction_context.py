import typing
from contextvars import ContextVar

from openfeature.evaluation_context import EvaluationContext

__all__ = [
    "TransactionContextPropagator",
    "NoopTransactionContextPropagator",
    "ContextVarTransactionContextPropagator",
]


class TransactionContextPropagator(typing.Protocol):
    def get_transaction_context(self) -> EvaluationContext: ...

    def set_transaction_context(self, context: EvaluationContext) -> None: ...


class NoopTransactionContextPropagator(TransactionContextPropagator):
    def get_transaction_context(self) -> EvaluationContext:
        return EvaluationContext()

    def set_transaction_context(self, context: EvaluationContext) -> None:
        pass


class ContextVarTransactionContextPropagator(TransactionContextPropagator):
    def __init__(self) -> None:
        self._contextvar = ContextVar(
            "transaction_context", default=EvaluationContext()
        )

    def get_transaction_context(self) -> EvaluationContext:
        return self._contextvar.get()

    def set_transaction_context(self, context: EvaluationContext) -> None:
        self._contextvar.set(context)

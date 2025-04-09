from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context.context_var_transaction_context_propagator import (
    ContextVarsTransactionContextPropagator,
)
from openfeature.transaction_context.no_op_transaction_context_propagator import (
    NoOpTransactionContextPropagator,
)
from openfeature.transaction_context.transaction_context_propagator import (
    TransactionContextPropagator,
)

__all__ = [
    "ContextVarsTransactionContextPropagator",
    "TransactionContextPropagator",
    "get_transaction_context",
    "set_transaction_context",
    "set_transaction_context_propagator",
]

_evaluation_transaction_context_propagator: TransactionContextPropagator = (
    NoOpTransactionContextPropagator()
)


def set_transaction_context_propagator(
    transaction_context_propagator: TransactionContextPropagator,
) -> None:
    global _evaluation_transaction_context_propagator
    _evaluation_transaction_context_propagator = transaction_context_propagator


def get_transaction_context() -> EvaluationContext:
    return _evaluation_transaction_context_propagator.get_transaction_context()


def set_transaction_context(evaluation_context: EvaluationContext) -> None:
    global _evaluation_transaction_context_propagator
    _evaluation_transaction_context_propagator.set_transaction_context(
        evaluation_context
    )

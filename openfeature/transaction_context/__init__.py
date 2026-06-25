import threading

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
    "clear_transaction_context_propagator",
    "get_transaction_context",
    "set_transaction_context",
    "set_transaction_context_propagator",
]

_evaluation_transaction_context_propagator: TransactionContextPropagator = (
    NoOpTransactionContextPropagator()
)
_propagator_lock = threading.RLock()


def set_transaction_context_propagator(
    transaction_context_propagator: TransactionContextPropagator,
) -> None:
    global _evaluation_transaction_context_propagator
    with _propagator_lock:
        _evaluation_transaction_context_propagator = transaction_context_propagator


def clear_transaction_context_propagator() -> None:
    set_transaction_context_propagator(NoOpTransactionContextPropagator())


def get_transaction_context() -> EvaluationContext:
    with _propagator_lock:
        propagator = _evaluation_transaction_context_propagator
        return propagator.get_transaction_context()


def set_transaction_context(evaluation_context: EvaluationContext) -> None:
    with _propagator_lock:
        propagator = _evaluation_transaction_context_propagator
        propagator.set_transaction_context(evaluation_context)

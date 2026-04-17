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
    "NoOpTransactionContextPropagator",
    "TransactionContextPropagator",
    "get_transaction_context",
    "set_transaction_context",
    "set_transaction_context_propagator",
]


def set_transaction_context_propagator(
    transaction_context_propagator: TransactionContextPropagator,
) -> None:
    from openfeature._api import _default_api  # noqa: PLC0415

    _default_api.set_transaction_context_propagator(transaction_context_propagator)


def get_transaction_context() -> EvaluationContext:
    from openfeature._api import _default_api  # noqa: PLC0415

    return _default_api.get_transaction_context()


def set_transaction_context(evaluation_context: EvaluationContext) -> None:
    from openfeature._api import _default_api  # noqa: PLC0415

    _default_api.set_transaction_context(evaluation_context)

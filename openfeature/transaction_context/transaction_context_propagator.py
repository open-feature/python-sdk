import typing

from openfeature.evaluation_context import EvaluationContext


class TransactionContextPropagator(typing.Protocol):
    def get_transaction_context(self) -> EvaluationContext: ...

    def set_transaction_context(
        self, transaction_context: EvaluationContext
    ) -> None: ...

import typing
from typing import TypeVar

from openfeature.evaluation_context import EvaluationContext

T = TypeVar("T", bound="TransactionContextPropagator")


class TransactionContextPropagator(typing.Protocol):
    def get_transaction_context(self) -> EvaluationContext: ...

    def set_transaction_context(
        self, transaction_context: EvaluationContext
    ) -> None: ...

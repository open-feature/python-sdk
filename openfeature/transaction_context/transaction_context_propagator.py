from abc import ABC, abstractmethod
from typing import TypeVar

from openfeature.evaluation_context import EvaluationContext

T = TypeVar("T", bound="TransactionContextPropagator")


class TransactionContextPropagator(ABC):
    @abstractmethod
    def get_transaction_context(self) -> EvaluationContext:
        pass

    @abstractmethod
    def set_transaction_context(self, transaction_context: EvaluationContext) -> None:
        pass

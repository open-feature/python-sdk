from abc import abstractmethod
from numbers import Number

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.provider.metadata import Metadata


class AbstractProvider:
    @abstractmethod
    def get_metadata(self) -> Metadata:
        pass

    @abstractmethod
    def get_boolean_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: EvaluationContext = EvaluationContext(),
    ):
        pass

    @abstractmethod
    def get_string_details(
        self,
        key: str,
        default_value: str,
        evaluation_context: EvaluationContext = EvaluationContext(),
    ):
        pass

    @abstractmethod
    def get_number_details(
        self,
        key: str,
        default_value: Number,
        evaluation_context: EvaluationContext = EvaluationContext(),
    ):
        pass

    @abstractmethod
    def get_object_details(
        self,
        key: str,
        default_value: dict,
        evaluation_context: EvaluationContext = EvaluationContext(),
    ):
        pass

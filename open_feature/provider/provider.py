import typing
from abc import abstractmethod

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.hooks.hook import Hook
from open_feature.provider.metadata import Metadata


class AbstractProvider:
    @abstractmethod
    def get_metadata(self) -> Metadata:
        pass

    @abstractmethod
    def get_provider_hooks(self) -> typing.List[Hook]:
        return []

    @abstractmethod
    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[bool]:
        pass

    @abstractmethod
    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[str]:
        pass

    @abstractmethod
    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[int]:
        pass

    @abstractmethod
    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[float]:
        pass

    @abstractmethod
    def resolve_object_details(
        self,
        flag_key: str,
        default_value: dict,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[dict]:
        pass

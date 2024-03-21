import typing
from abc import abstractmethod

from openfeature._event_support import run_handlers_for_provider
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider
from openfeature.provider.metadata import Metadata


class AbstractProvider(FeatureProvider):
    def initialize(self, evaluation_context: EvaluationContext) -> None:
        pass

    def shutdown(self) -> None:
        pass

    @abstractmethod
    def get_metadata(self) -> Metadata:
        pass

    def get_provider_hooks(self) -> typing.List[Hook]:
        return []

    @abstractmethod
    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        pass

    @abstractmethod
    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        pass

    @abstractmethod
    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        pass

    @abstractmethod
    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        pass

    @abstractmethod
    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[dict, list],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[typing.Union[dict, list]]:
        pass

    def emit_provider_ready(self, details: ProviderEventDetails) -> None:
        self.emit(ProviderEvent.PROVIDER_READY, details)

    def emit_provider_configuration_changed(
        self, details: ProviderEventDetails
    ) -> None:
        self.emit(ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, details)

    def emit_provider_error(self, details: ProviderEventDetails) -> None:
        self.emit(ProviderEvent.PROVIDER_ERROR, details)

    def emit_provider_stale(self, details: ProviderEventDetails) -> None:
        self.emit(ProviderEvent.PROVIDER_STALE, details)

    def emit(self, event: ProviderEvent, details: ProviderEventDetails) -> None:
        run_handlers_for_provider(self, event, details)

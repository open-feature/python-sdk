from __future__ import annotations

import typing
from abc import abstractmethod
from collections.abc import Sequence
from enum import Enum

from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.hook import Hook

from .metadata import Metadata

if typing.TYPE_CHECKING:
    from openfeature.flag_evaluation import FlagValueType

__all__ = ["AbstractProvider", "FeatureProvider", "Metadata", "ProviderStatus"]


class ProviderStatus(Enum):
    NOT_READY = "NOT_READY"
    READY = "READY"
    ERROR = "ERROR"
    STALE = "STALE"
    FATAL = "FATAL"


class FeatureProvider(typing.Protocol):  # pragma: no cover
    def attach(
        self,
        on_emit: typing.Callable[
            [FeatureProvider, ProviderEvent, ProviderEventDetails], None
        ],
    ) -> None: ...

    def detach(self) -> None: ...

    def initialize(self, evaluation_context: EvaluationContext) -> None: ...

    def shutdown(self) -> None: ...

    def get_metadata(self) -> Metadata: ...

    def get_provider_hooks(self) -> list[Hook]: ...

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]: ...

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]: ...

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]: ...

    async def resolve_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]: ...

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]: ...

    async def resolve_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]: ...

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]: ...

    async def resolve_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]: ...

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]: ...

    async def resolve_object_details_async(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]: ...


class AbstractProvider(FeatureProvider):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        # this makes sure to invoke the parent of `FeatureProvider` -> `object`
        super(FeatureProvider, self).__init__(*args, **kwargs)

    def attach(
        self,
        on_emit: typing.Callable[
            [FeatureProvider, ProviderEvent, ProviderEventDetails], None
        ],
    ) -> None:
        self._on_emit = on_emit

    def detach(self) -> None:
        if hasattr(self, "_on_emit"):
            del self._on_emit

    def initialize(self, evaluation_context: EvaluationContext) -> None:
        pass

    def shutdown(self) -> None:
        pass

    @abstractmethod
    def get_metadata(self) -> Metadata:
        pass

    def get_provider_hooks(self) -> list[Hook]:
        return []

    @abstractmethod
    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        pass

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return self.resolve_boolean_details(flag_key, default_value, evaluation_context)

    @abstractmethod
    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        pass

    async def resolve_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return self.resolve_string_details(flag_key, default_value, evaluation_context)

    @abstractmethod
    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        pass

    async def resolve_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return self.resolve_integer_details(flag_key, default_value, evaluation_context)

    @abstractmethod
    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        pass

    async def resolve_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return self.resolve_float_details(flag_key, default_value, evaluation_context)

    @abstractmethod
    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]:
        pass

    async def resolve_object_details_async(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]:
        return self.resolve_object_details(flag_key, default_value, evaluation_context)

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
        if hasattr(self, "_on_emit"):
            self._on_emit(self, event, details)

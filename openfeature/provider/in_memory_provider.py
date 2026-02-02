from __future__ import annotations

import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from openfeature._backports.strenum import StrEnum
from openfeature.evaluation_context import EvaluationContext, EvaluationContextAttribute
from openfeature.exception import ErrorCode
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.provider import AbstractProvider, Metadata
from openfeature.track import TrackingEventDetails

if typing.TYPE_CHECKING:
    from openfeature.flag_evaluation import FlagMetadata, FlagValueType
    from openfeature.hook import Hook

PASSED_IN_DEFAULT = "Passed in default"


@dataclass
class InMemoryMetadata(Metadata):
    name: str = "In-Memory Provider"

@dataclass
class InMemoryTrackingEvent():
    value: float | None = None
    details: dict[str, typing.Any] = field(default_factory=dict)
    eval_context_attributes: Mapping[str, EvaluationContextAttribute] = field(default_factory=dict)



T_co = typing.TypeVar("T_co", covariant=True)


@dataclass(frozen=True)
class InMemoryFlag(typing.Generic[T_co]):
    class State(StrEnum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    default_variant: str
    variants: dict[str, T_co]
    flag_metadata: FlagMetadata = field(default_factory=dict)
    state: State = State.ENABLED
    context_evaluator: (
        Callable[[InMemoryFlag[T_co], EvaluationContext], FlagResolutionDetails[T_co]]
        | None
    ) = None

    def resolve(
        self, evaluation_context: EvaluationContext | None
    ) -> FlagResolutionDetails[T_co]:
        if self.context_evaluator:
            return self.context_evaluator(
                self, evaluation_context or EvaluationContext()
            )

        return FlagResolutionDetails(
            value=self.variants[self.default_variant],
            reason=Reason.STATIC,
            variant=self.default_variant,
            flag_metadata=self.flag_metadata,
        )


FlagStorage = dict[str, InMemoryFlag[typing.Any]]

TrackingStorage = dict[str, InMemoryTrackingEvent]

V = typing.TypeVar("V")


class InMemoryProvider(AbstractProvider):
    _flags: FlagStorage
    _tracking_events: TrackingStorage
    # tracking_events defaults to an empty dict
    def __init__(self, flags: FlagStorage, tracking_events: TrackingStorage | None = None) -> None:
        self._flags = flags.copy()
        if tracking_events is not None:
            self._tracking_events = tracking_events.copy()
        else:
            self._tracking_events = {}

    def get_metadata(self) -> Metadata:
        return InMemoryMetadata()

    def get_provider_hooks(self) -> list[Hook]:
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        return self._resolve(flag_key, default_value, evaluation_context)

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        return await self._resolve_async(flag_key, default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return self._resolve(flag_key, default_value, evaluation_context)

    async def resolve_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return await self._resolve_async(flag_key, default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return self._resolve(flag_key, default_value, evaluation_context)

    async def resolve_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return await self._resolve_async(flag_key, default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return self._resolve(flag_key, default_value, evaluation_context)

    async def resolve_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return await self._resolve_async(flag_key, default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return self._resolve(flag_key, default_value, evaluation_context)

    async def resolve_object_details_async(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return await self._resolve_async(flag_key, default_value, evaluation_context)

    def _resolve(
        self,
        flag_key: str,
        default_value: V,
        evaluation_context: EvaluationContext | None,
    ) -> FlagResolutionDetails[V]:
        flag = self._flags.get(flag_key)
        if flag is None:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.FLAG_NOT_FOUND,
                error_message=f"Flag '{flag_key}' not found",
            )
        return flag.resolve(evaluation_context)

    async def _resolve_async(
        self,
        flag_key: str,
        default_value: V,
        evaluation_context: EvaluationContext | None,
    ) -> FlagResolutionDetails[V]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def track(self, tracking_event_name: str, evaluation_context: EvaluationContext | None = None, tracking_event_details: TrackingEventDetails | None = None) -> None:
        value = tracking_event_details.value if tracking_event_details is not None else None
        details = tracking_event_details.attributes if tracking_event_details is not None else {}
        eval_context_attributes = evaluation_context.attributes if evaluation_context is not None else {}

        self._tracking_events[tracking_event_name] = InMemoryTrackingEvent(
            value=value,
            details=details,
            eval_context_attributes=eval_context_attributes,
        )

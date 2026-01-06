import typing
from collections.abc import Mapping
from dataclasses import dataclass

from openfeature.exception import ErrorCode
from openfeature.flag_evaluation import FlagEvaluationDetails, Reason
from openfeature.hook import HookContext
from openfeature.telemetry.attributes import TelemetryAttribute
from openfeature.telemetry.body import TelemetryBodyField
from openfeature.telemetry.metadata import TelemetryFlagMetadata

__all__ = [
    "EvaluationEvent",
    "TelemetryAttribute",
    "TelemetryBodyField",
    "TelemetryFlagMetadata",
    "create_evaluation_event",
]

FLAG_EVALUATION_EVENT_NAME = "feature_flag.evaluation"

T_co = typing.TypeVar("T_co", covariant=True)


@dataclass
class EvaluationEvent(typing.Generic[T_co]):
    name: str
    attributes: Mapping[TelemetryAttribute, str | T_co]
    body: Mapping[TelemetryBodyField, T_co]


def create_evaluation_event(
    hook_context: HookContext, details: FlagEvaluationDetails[T_co]
) -> EvaluationEvent[T_co]:
    attributes = {
        TelemetryAttribute.KEY: details.flag_key,
        TelemetryAttribute.EVALUATION_REASON: (
            details.reason or Reason.UNKNOWN
        ).lower(),
    }
    body = {}

    if variant := details.variant:
        attributes[TelemetryAttribute.VARIANT] = variant
    else:
        body[TelemetryBodyField.VALUE] = details.value

    context_id = details.flag_metadata.get(
        TelemetryFlagMetadata.CONTEXT_ID, hook_context.evaluation_context.targeting_key
    )
    if context_id:
        attributes[TelemetryAttribute.CONTEXT_ID] = typing.cast("str", context_id)

    if set_id := details.flag_metadata.get(TelemetryFlagMetadata.FLAG_SET_ID):
        attributes[TelemetryAttribute.SET_ID] = typing.cast("str", set_id)

    if version := details.flag_metadata.get(TelemetryFlagMetadata.VERSION):
        attributes[TelemetryAttribute.VERSION] = typing.cast("str", version)

    if metadata := hook_context.provider_metadata:
        attributes[TelemetryAttribute.PROVIDER_NAME] = metadata.name

    if details.reason == Reason.ERROR:
        attributes[TelemetryAttribute.ERROR_TYPE] = (
            details.error_code or ErrorCode.GENERAL
        ).lower()

        if err_msg := details.error_message:
            attributes[TelemetryAttribute.EVALUATION_ERROR_MESSAGE] = err_msg

    return EvaluationEvent(
        name=FLAG_EVALUATION_EVENT_NAME,
        attributes=attributes,
        body=body,
    )

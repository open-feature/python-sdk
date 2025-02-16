from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import ErrorCode
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType, Reason
from openfeature.hook import HookContext
from openfeature.provider import Metadata
from openfeature.telemetry import (
    TelemetryAttribute,
    TelemetryBodyField,
    TelemetryFlagMetadata,
    create_evaluation_event,
)


def test_create_evaluation_event():
    # given
    hook_context = HookContext(
        flag_key="flag_key",
        flag_type=FlagType.BOOLEAN,
        default_value=True,
        evaluation_context=EvaluationContext(),
        provider_metadata=Metadata(name="test_provider"),
    )
    details = FlagEvaluationDetails(
        flag_key=hook_context.flag_key,
        value=False,
        reason=Reason.CACHED,
    )

    # when
    event = create_evaluation_event(hook_context=hook_context, details=details)

    # then
    assert event.name == "feature_flag.evaluation"
    assert event.attributes[TelemetryAttribute.KEY] == "flag_key"
    assert event.attributes[TelemetryAttribute.EVALUATION_REASON] == "cached"
    assert event.attributes[TelemetryAttribute.PROVIDER_NAME] == "test_provider"
    assert event.body[TelemetryBodyField.VALUE] is False


def test_create_evaluation_event_with_variant():
    # given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, EvaluationContext())
    details = FlagEvaluationDetails(
        flag_key=hook_context.flag_key,
        value=True,
        variant="true",
    )

    # when
    event = create_evaluation_event(hook_context=hook_context, details=details)

    # then
    assert event.name == "feature_flag.evaluation"
    assert event.attributes[TelemetryAttribute.KEY] == "flag_key"
    assert event.attributes[TelemetryAttribute.VARIANT] == "true"
    assert event.attributes[TelemetryAttribute.EVALUATION_REASON] == "unknown"


def test_create_evaluation_event_with_metadata():
    # given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, EvaluationContext())
    details = FlagEvaluationDetails(
        flag_key=hook_context.flag_key,
        value=False,
        flag_metadata={
            TelemetryFlagMetadata.CONTEXT_ID: "5157782b-2203-4c80-a857-dbbd5e7761db",
            TelemetryFlagMetadata.FLAG_SET_ID: "proj-1",
            TelemetryFlagMetadata.VERSION: "v1",
        },
    )

    # when
    event = create_evaluation_event(hook_context=hook_context, details=details)

    # then
    assert (
        event.attributes[TelemetryAttribute.CONTEXT_ID]
        == "5157782b-2203-4c80-a857-dbbd5e7761db"
    )
    assert event.attributes[TelemetryAttribute.SET_ID] == "proj-1"
    assert event.attributes[TelemetryAttribute.VERSION] == "v1"


def test_create_evaluation_event_with_error():
    # given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, EvaluationContext())
    details = FlagEvaluationDetails(
        flag_key=hook_context.flag_key,
        value=False,
        reason=Reason.ERROR,
        error_code=ErrorCode.FLAG_NOT_FOUND,
        error_message="flag error",
    )

    # when
    event = create_evaluation_event(hook_context=hook_context, details=details)

    # then
    assert event.attributes[TelemetryAttribute.EVALUATION_REASON] == "error"
    assert event.attributes[TelemetryAttribute.ERROR_TYPE] == "flag_not_found"
    assert event.attributes[TelemetryAttribute.EVALUATION_ERROR_MESSAGE] == "flag error"

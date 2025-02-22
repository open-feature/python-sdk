from openfeature._backports.strenum import StrEnum


class TelemetryAttribute(StrEnum):
    """
    The attributes of an OpenTelemetry compliant event for flag evaluation.

    See: https://opentelemetry.io/docs/specs/semconv/feature-flags/feature-flags-logs/
    """

    CONTEXT_ID = "feature_flag.context.id"
    ERROR_TYPE = "error.type"
    EVALUATION_ERROR_MESSAGE = "feature_flag.evaluation.error.message"
    EVALUATION_REASON = "feature_flag.evaluation.reason"
    KEY = "feature_flag.key"
    PROVIDER_NAME = "feature_flag.provider_name"
    SET_ID = "feature_flag.set.id"
    VARIANT = "feature_flag.variant"
    VERSION = "feature_flag.version"

from openfeature._backports.strenum import StrEnum


class TelemetryBodyField(StrEnum):
    """
    OpenTelemetry event body fields.

    See: https://opentelemetry.io/docs/specs/semconv/feature-flags/feature-flags-logs/
    """

    VALUE = "value"

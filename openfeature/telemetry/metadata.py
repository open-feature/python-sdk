from openfeature._backports.strenum import StrEnum


class TelemetryFlagMetadata(StrEnum):
    """
    Well-known flag metadata attributes for telemetry events.

    See: https://openfeature.dev/specification/appendix-d/#flag-metadata
    """

    CONTEXT_ID = "contextId"
    FLAG_SET_ID = "flagSetId"
    VERSION = "version"

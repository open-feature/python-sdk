from enum import Enum


class Reason(Enum):
    CACHED = "CACHED"
    DEFAULT = "DEFAULT"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    STATIC = "STATIC"
    SPLIT = "SPLIT"
    TARGETING_MATCH = "TARGETING_MATCH"
    UNKNOWN = "UNKNOWN"

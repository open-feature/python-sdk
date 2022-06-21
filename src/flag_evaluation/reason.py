from enum import Enum


class Reason(Enum):
    DISABLED = "DISABLED"
    SPLIT = "SPLIT"
    TARGETING_MATCH = "TARGETING_MATCH"
    DEFAULT = "DEFAULT"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

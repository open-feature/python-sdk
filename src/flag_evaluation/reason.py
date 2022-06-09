from enum import Enum


class Reason(Enum):
    DISABLED = 1
    SPLIT = 2
    TARGETING_MATCH = 3
    DEFAULT = 4
    UNKNOWN = 5
    ERROR = 6

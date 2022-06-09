from enum import Enum


class ErrorCode(Enum):
    PROVIDER_NOT_READY = 1
    FLAG_NOT_FOUND = 2
    PARSE_ERROR = 3
    TYPE_MISMATCH = 4
    GENERAL = 5

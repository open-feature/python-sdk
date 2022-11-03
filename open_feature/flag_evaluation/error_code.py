from enum import Enum


class ErrorCode(Enum):
    PROVIDER_NOT_READY = "PROVIDER_NOT_READY"
    FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    PARSE_ERROR = "PARSE_ERROR"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    TARGETING_KEY_MISSING = "TARGETING_KEY_MISSING"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    GENERAL = "GENERAL"

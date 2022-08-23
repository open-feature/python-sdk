from enum import Enum


class HookType(Enum):
    BEFORE = "before"
    AFTER = "after"
    FINALLY_AFTER = "finally_after"
    ERROR = "error"

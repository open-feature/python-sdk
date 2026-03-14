from openfeature.hook.hook import Hook, HookContext, HookData, HookHints, HookType
from openfeature.hook.logging_hook import LoggingHook

__all__ = [
    "Hook",
    "HookContext",
    "HookData",
    "HookHints",
    "HookType",
    "LoggingHook",
    "add_hooks",
    "clear_hooks",
    "get_hooks",
]

_hooks: list[Hook] = []


def add_hooks(hooks: list[Hook]) -> None:
    global _hooks
    _hooks = _hooks + hooks


def clear_hooks() -> None:
    global _hooks
    _hooks = []


def get_hooks() -> list[Hook]:
    return _hooks

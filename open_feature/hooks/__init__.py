import typing

from open_feature.hooks.hook import Hook


_hooks: typing.List[Hook] = []


def add_api_hooks(hooks: typing.List[Hook]):
    global _hooks
    _hooks = _hooks + hooks


def clear_api_hooks():
    global _hooks
    _hooks = []


def api_hooks() -> typing.List[Hook]:
    global _hooks
    return _hooks

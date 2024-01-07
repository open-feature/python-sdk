import typing


class MappingProxyType(dict):
    """
    MappingProxyType is an immutable dictionary type, written to
    support Python 3.8 with easy transition to 3.12 upon removal
    of older versions.

    See: https://stackoverflow.com/a/72474524

    When upgrading to Python 3.12, you can update all references
    from:
    `from openfeature.immutable_dict.mapping_proxy_type import MappingProxyType`

    to:
    `from types import MappingProxyType`
    """

    def __hash__(self) -> int:  # type:ignore[override]
        return id(self)

    def _immutable(self, *args: typing.Any, **kws: typing.Any) -> typing.NoReturn:
        raise TypeError("immutable instance of dictionary")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable  # type:ignore[assignment]
    setdefault = _immutable  # type:ignore[assignment]
    pop = _immutable  # type:ignore[assignment]
    popitem = _immutable

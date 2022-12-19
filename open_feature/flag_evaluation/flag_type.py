import typing
from enum import Enum


class FlagType(Enum):
    BOOLEAN = bool
    STRING = str
    OBJECT = typing.Union[dict, list]
    FLOAT = float
    INTEGER = int

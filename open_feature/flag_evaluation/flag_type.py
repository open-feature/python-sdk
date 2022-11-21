from enum import Enum


class FlagType(Enum):
    BOOLEAN = bool
    STRING = str
    OBJECT = dict
    FLOAT = float
    INTEGER = int

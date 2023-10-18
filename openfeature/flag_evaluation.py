from __future__ import annotations

import typing
from dataclasses import dataclass, field

from openfeature._backports.strenum import StrEnum
from openfeature.exception import ErrorCode

if typing.TYPE_CHECKING:  # resolves a circular dependency in type annotations
    from openfeature.hook import Hook


class FlagType(StrEnum):
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    OBJECT = "OBJECT"
    FLOAT = "FLOAT"
    INTEGER = "INTEGER"


class Reason(StrEnum):
    CACHED = "CACHED"
    DEFAULT = "DEFAULT"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    STATIC = "STATIC"
    SPLIT = "SPLIT"
    TARGETING_MATCH = "TARGETING_MATCH"
    UNKNOWN = "UNKNOWN"


FlagMetadata = typing.Mapping[str, typing.Any]

T = typing.TypeVar("T", covariant=True)


@dataclass
class FlagEvaluationDetails(typing.Generic[T]):
    flag_key: str
    value: T
    variant: typing.Optional[str] = None
    flag_metadata: FlagMetadata = field(default_factory=dict)
    reason: typing.Optional[Reason] = None
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None


@dataclass
class FlagEvaluationOptions:
    hooks: typing.List[Hook] = field(default_factory=list)
    hook_hints: dict = field(default_factory=dict)


U = typing.TypeVar("U", covariant=True)


@dataclass
class FlagResolutionDetails(typing.Generic[U]):
    value: U
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None
    reason: typing.Optional[Reason] = None
    variant: typing.Optional[str] = None
    flag_metadata: FlagMetadata = field(default_factory=dict)

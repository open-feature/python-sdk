from __future__ import annotations

import typing
from dataclasses import dataclass, field

from openfeature._backports.strenum import StrEnum
from openfeature.exception import ErrorCode

if typing.TYPE_CHECKING:  # pragma: no cover
    # resolves a circular dependency in type annotations
    from openfeature.hook import Hook, HookHints


__all__ = [
    "FlagType",
    "Reason",
    "FlagMetadata",
    "FlagEvaluationDetails",
    "FlagEvaluationOptions",
    "FlagResolutionDetails",
]


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

T_co = typing.TypeVar("T_co", covariant=True)


@dataclass
class FlagEvaluationDetails(typing.Generic[T_co]):
    flag_key: str
    value: T_co
    variant: typing.Optional[str] = None
    flag_metadata: FlagMetadata = field(default_factory=dict)
    reason: typing.Optional[typing.Union[str, Reason]] = None
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None


@dataclass
class FlagEvaluationOptions:
    hooks: typing.List[Hook] = field(default_factory=list)
    hook_hints: HookHints = field(default_factory=dict)


U_co = typing.TypeVar("U_co", covariant=True)


@dataclass
class FlagResolutionDetails(typing.Generic[U_co]):
    value: U_co
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None
    reason: typing.Optional[typing.Union[str, Reason]] = None
    variant: typing.Optional[str] = None
    flag_metadata: FlagMetadata = field(default_factory=dict)

    def raise_for_error(self) -> None:
        if self.error_code:
            raise ErrorCode.to_exception(self.error_code, self.error_message or "")
        return None

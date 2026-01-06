from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from openfeature._backports.strenum import StrEnum
from openfeature.exception import ErrorCode, OpenFeatureError

if typing.TYPE_CHECKING:  # pragma: no cover
    # resolves a circular dependency in type annotations
    from openfeature.hook import Hook, HookHints


__all__ = [
    "FlagEvaluationDetails",
    "FlagEvaluationOptions",
    "FlagMetadata",
    "FlagResolutionDetails",
    "FlagType",
    "Reason",
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
    SPLIT = "SPLIT"
    STATIC = "STATIC"
    STALE = "STALE"
    TARGETING_MATCH = "TARGETING_MATCH"
    UNKNOWN = "UNKNOWN"


FlagMetadata = Mapping[str, bool | int | float | str]
FlagValueType = (
    bool
    | int
    | float
    | str
    | Sequence["FlagValueType"]
    | Mapping[str, "FlagValueType"]
)

T_co = typing.TypeVar("T_co", covariant=True)


@dataclass
class FlagEvaluationDetails(typing.Generic[T_co]):
    flag_key: str
    value: T_co
    variant: str | None = None
    flag_metadata: FlagMetadata = field(default_factory=dict)
    reason: str | Reason | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None

    def get_exception(self) -> OpenFeatureError | None:
        if self.error_code:
            return ErrorCode.to_exception(self.error_code, self.error_message or "")
        return None


@dataclass
class FlagEvaluationOptions:
    hooks: list[Hook] = field(default_factory=list)
    hook_hints: HookHints = field(default_factory=dict)


U_co = typing.TypeVar("U_co", covariant=True)


@dataclass
class FlagResolutionDetails(typing.Generic[U_co]):
    value: U_co
    error_code: ErrorCode | None = None
    error_message: str | None = None
    reason: str | Reason | None = None
    variant: str | None = None
    flag_metadata: FlagMetadata = field(default_factory=dict)

    def raise_for_error(self) -> None:
        if self.error_code:
            raise ErrorCode.to_exception(self.error_code, self.error_message or "")
        return None

    def to_flag_evaluation_details(self, flag_key: str) -> FlagEvaluationDetails[U_co]:
        return FlagEvaluationDetails(
            flag_key=flag_key,
            value=self.value,
            variant=self.variant,
            flag_metadata=self.flag_metadata,
            reason=self.reason,
            error_code=self.error_code,
            error_message=self.error_message,
        )

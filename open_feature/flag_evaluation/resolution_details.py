import typing
from dataclasses import dataclass

from open_feature.exception.error_code import ErrorCode
from open_feature.flag_evaluation.reason import Reason

T = typing.TypeVar("T", covariant=True)


@dataclass
class FlagResolutionDetails(typing.Generic[T]):
    value: T
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None
    reason: typing.Optional[Reason] = None
    variant: typing.Optional[str] = None
    flag_metadata: typing.Optional[str] = None

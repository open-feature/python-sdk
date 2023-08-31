import typing
from dataclasses import dataclass

from open_feature.exception import ErrorCode
from open_feature.flag_evaluation.reason import Reason

T = typing.TypeVar("T", covariant=True)


@dataclass
class FlagEvaluationDetails(typing.Generic[T]):
    flag_key: str
    value: T
    variant: typing.Optional[str] = None
    reason: typing.Optional[Reason] = None
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None

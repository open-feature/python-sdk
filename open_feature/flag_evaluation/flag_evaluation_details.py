import typing
from dataclasses import dataclass

from open_feature.exception.error_code import ErrorCode
from open_feature.flag_evaluation.reason import Reason


@dataclass
class FlagEvaluationDetails:
    flag_key: str
    value: typing.Any
    variant: str = None
    reason: Reason = None
    error_code: ErrorCode = None
    error_message: typing.Optional[str] = None

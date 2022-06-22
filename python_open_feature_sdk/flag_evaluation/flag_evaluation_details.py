from python_open_feature_sdk.flag_evaluation.error_code import ErrorCode
from python_open_feature_sdk.flag_evaluation.reason import Reason


class FlagEvaluationDetails:
    def __init__(
        self,
        key: str,
        value,
        reason: Reason,
        error_code: ErrorCode = None,
        variant=None,
    ):
        self.key = key
        self.value = value
        self.reason = reason
        self.error_code = error_code
        self.variant = variant

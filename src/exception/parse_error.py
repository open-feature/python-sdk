from src.exception.open_feature_error import OpenFeatureError
from src.flag_evaluation.error_code import ErrorCode


class ParseError(OpenFeatureError):
    def __init__(self, error_message: str = None):
        self.error_message = error_message
        self.error_code = ErrorCode.PARSE_ERROR

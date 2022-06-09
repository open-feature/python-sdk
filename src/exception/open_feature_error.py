from src.flag_evaluation.error_code import ErrorCode


class OpenFeatureError(Exception):
    def __init__(
        self, error_message: str = None, error_code: ErrorCode = None
    ):
        self.error_message = error_message
        self.error_code = error_code

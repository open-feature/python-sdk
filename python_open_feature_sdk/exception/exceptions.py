from python_open_feature_sdk.flag_evaluation.error_code import ErrorCode

"""
"""


class OpenFeatureError(Exception):
    def __init__(self, error_message: str = None, error_code: ErrorCode = None):
        self.error_message = error_message
        self.error_code = error_code


"""
"""


class FlagNotFoundError(OpenFeatureError):
    def __init__(self, error_message: str = None):
        super().__init__(error_message, ErrorCode.FLAG_NOT_FOUND)


"""
"""


class GeneralError(OpenFeatureError):
    def __init__(self, error_message: str = None):
        super().__init__(error_message, ErrorCode.GENERAL)


"""
"""


class ParseError(OpenFeatureError):
    def __init__(self, error_message: str = None):
        super().__init__(error_message, ErrorCode.PARSE_ERROR)


"""
"""


class TypeMismatchError(OpenFeatureError):
    def __init__(self, error_message: str = None):
        super().__init__(error_message, ErrorCode.TYPE_MISMATCH)

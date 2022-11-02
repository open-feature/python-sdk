import typing

from open_feature.exception.error_code import ErrorCode


class OpenFeatureError(Exception):
    """
    A generic open feature exception, this exception should not be raised. Instead
    the more specific exceptions extending this one should be used.
    """

    def __init__(
        self, error_message: typing.Optional[str] = None, error_code: ErrorCode = None
    ):
        """
        Constructor for the generic OpenFeatureError.
        @param error_message: an optional string message representing why the
        error has been raised
        @param error_code: the ErrorCode string enum value for the type of error
        @return: the generic OpenFeatureError exception
        """
        self.error_message = error_message
        self.error_code = error_code


class FlagNotFoundError(OpenFeatureError):
    """
    This exception should be raised when the provider cannot find a flag with the
    key provided by the user.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the FlagNotFoundError.  The error code for
        this type of exception is ErrorCode.FLAG_NOT_FOUND.
        @param error_message: an optional string message representing
        why the error has been raised
        @return: the generic FlagNotFoundError exception
        """
        super().__init__(error_message, ErrorCode.FLAG_NOT_FOUND)


class GeneralError(OpenFeatureError):
    """
    This exception should be raised when the for an exception within the open
    feature python sdk.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the GeneralError.  The error code for this type of exception
        is ErrorCode.GENERAL.
        @param error_message: an optional string message representing why the error
        has been raised
        @return: the generic GeneralError exception
        """
        super().__init__(error_message, ErrorCode.GENERAL)


class ParseError(OpenFeatureError):
    """
    This exception should be raised when the flag returned by the provider cannot
    be parsed into a FlagEvaluationDetails object.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the ParseError. The error code for this type of exception
        is ErrorCode.PARSE_ERROR.
        @param error_message: an optional string message representing why the
        error has been raised
        @return: the generic ParseError exception
        """
        super().__init__(error_message, ErrorCode.PARSE_ERROR)


class TypeMismatchError(OpenFeatureError):
    """
    This exception should be raised when the flag returned by the provider does
    not match the type requested by the user.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the TypeMismatchError. The error code for this type of
        exception is ErrorCode.TYPE_MISMATCH.
        @param error_message: an optional string message representing why the
        error has been raised
        @return: the generic TypeMismatchError exception
        """
        super().__init__(error_message, ErrorCode.TYPE_MISMATCH)


class TargetingKeyMissingError(OpenFeatureError):
    """
    This exception should be raised when the provider requires a targeting key
    but one was not provided in the evaluation context.
    """

    def __init__(self, error_message: str = None):
        """
        Constructor for the TargetingKeyMissingError. The error code for this type of
        exception is ErrorCode.TARGETING_KEY_MISSING.
        @param error_message: a string message representing why the error has been
        raised
        """
        super().__init__(error_message, ErrorCode.TARGETING_KEY_MISSING)


class InvalidContextError(OpenFeatureError):
    """
    This exception should be raised when the evaluation context does not meet provider
    requirements.
    """

    def __init__(self, error_message: str = None):
        """
        Constructor for the InvalidContextError. The error code for this type of
        exception is ErrorCode.INVALID_CONTEXT.
        @param error_message: a string message representing why the error has been
        raised
        """
        super().__init__(error_message, ErrorCode.INVALID_CONTEXT)

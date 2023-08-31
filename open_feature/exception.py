import typing
from enum import Enum


class ErrorCode(Enum):
    PROVIDER_NOT_READY = "PROVIDER_NOT_READY"
    FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    PARSE_ERROR = "PARSE_ERROR"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    TARGETING_KEY_MISSING = "TARGETING_KEY_MISSING"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    GENERAL = "GENERAL"


class OpenFeatureError(Exception):
    """
    A generic open feature exception, this exception should not be raised. Instead
    the more specific exceptions extending this one should be used.
    """

    def __init__(
        self, error_code: ErrorCode, error_message: typing.Optional[str] = None
    ):
        """
        Constructor for the generic OpenFeatureError.
        @param error_message: an optional string message representing why the
        error has been raised
        @param error_code: the ErrorCode string enum value for the type of error
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
        """
        super().__init__(ErrorCode.FLAG_NOT_FOUND, error_message)


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
        """
        super().__init__(ErrorCode.GENERAL, error_message)


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
        """
        super().__init__(ErrorCode.PARSE_ERROR, error_message)


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
        """
        super().__init__(ErrorCode.TYPE_MISMATCH, error_message)


class TargetingKeyMissingError(OpenFeatureError):
    """
    This exception should be raised when the provider requires a targeting key
    but one was not provided in the evaluation context.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the TargetingKeyMissingError. The error code for this type of
        exception is ErrorCode.TARGETING_KEY_MISSING.
        @param error_message: a string message representing why the error has been
        raised
        """
        super().__init__(ErrorCode.TARGETING_KEY_MISSING, error_message)


class InvalidContextError(OpenFeatureError):
    """
    This exception should be raised when the evaluation context does not meet provider
    requirements.
    """

    def __init__(self, error_message: typing.Optional[str]):
        """
        Constructor for the InvalidContextError. The error code for this type of
        exception is ErrorCode.INVALID_CONTEXT.
        @param error_message: a string message representing why the error has been
        raised
        """
        super().__init__(ErrorCode.INVALID_CONTEXT, error_message)

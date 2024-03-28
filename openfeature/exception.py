from __future__ import annotations

import typing
from collections.abc import Mapping
from enum import Enum

__all__ = [
    "OpenFeatureError",
    "ProviderNotReadyError",
    "ProviderFatalError",
    "FlagNotFoundError",
    "GeneralError",
    "ParseError",
    "TypeMismatchError",
    "TargetingKeyMissingError",
    "InvalidContextError",
    "ErrorCode",
]


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


class ProviderNotReadyError(OpenFeatureError):
    """
    This exception should be raised when the provider is not ready to be used.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the ProviderNotReadyError. The error code for this type of
        exception is ErrorCode.PROVIDER_NOT_READY.
        @param error_message: a string message representing why the error has been
        raised
        """
        super().__init__(ErrorCode.PROVIDER_NOT_READY, error_message)


class ProviderFatalError(OpenFeatureError):
    """
    This exception should be raised when the provider encounters a fatal error.
    """

    def __init__(self, error_message: typing.Optional[str] = None):
        """
        Constructor for the ProviderFatalError. The error code for this type of
        exception is ErrorCode.PROVIDER_FATAL.
        @param error_message: a string message representing why the error has been
        raised
        """
        super().__init__(ErrorCode.PROVIDER_FATAL, error_message)


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


class ErrorCode(Enum):
    PROVIDER_NOT_READY = "PROVIDER_NOT_READY"
    PROVIDER_FATAL = "PROVIDER_FATAL"
    FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    PARSE_ERROR = "PARSE_ERROR"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    TARGETING_KEY_MISSING = "TARGETING_KEY_MISSING"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    GENERAL = "GENERAL"

    __exceptions__: Mapping[str, typing.Callable[[str], OpenFeatureError]] = {
        PROVIDER_NOT_READY: ProviderNotReadyError,
        PROVIDER_FATAL: ProviderFatalError,
        FLAG_NOT_FOUND: FlagNotFoundError,
        PARSE_ERROR: ParseError,
        TYPE_MISMATCH: TypeMismatchError,
        TARGETING_KEY_MISSING: TargetingKeyMissingError,
        INVALID_CONTEXT: InvalidContextError,
        GENERAL: GeneralError,
    }

    @classmethod
    def to_exception(
        cls, error_code: ErrorCode, error_message: str
    ) -> OpenFeatureError:
        exc = cls.__exceptions__.get(error_code.value, GeneralError)
        return exc(error_message)

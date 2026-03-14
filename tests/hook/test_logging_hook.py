from unittest.mock import MagicMock

import pytest

from openfeature.client import ClientMetadata
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import ErrorCode, FlagNotFoundError
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType
from openfeature.hook import HookContext, LoggingHook
from openfeature.provider.metadata import Metadata


@pytest.fixture()
def hook_context():
    return HookContext(
        flag_key="my-flag",
        flag_type=FlagType.BOOLEAN,
        default_value=False,
        evaluation_context=EvaluationContext("user-1", {"env": "prod"}),
        client_metadata=ClientMetadata(domain="my-domain"),
        provider_metadata=Metadata(name="my-provider"),
    )


def test_before_calls_debug_with_stage(hook_context):
    mock_logger = MagicMock()
    hook = LoggingHook(logger=mock_logger)
    hook.before(hook_context, hints={})
    mock_logger.debug.assert_called_with(
        "Before stage %s",
        {
            "stage": "before",
            "flag_key": "my-flag",
            "default_value": False,
            "domain": "my-domain",
            "provider_name": "my-provider",
        },
    )


def test_after_calls_debug_with_stage(hook_context):
    mock_logger = MagicMock()
    hook = LoggingHook(logger=mock_logger)
    details = FlagEvaluationDetails(
        flag_key="my-flag",
        value=True,
        variant="on",
        reason="STATIC",
    )
    hook.after(hook_context, details, hints={})

    mock_logger.debug.assert_called_with(
        "After stage %s",
        {
            "stage": "after",
            "flag_key": "my-flag",
            "default_value": False,
            "domain": "my-domain",
            "provider_name": "my-provider",
            "reason": "STATIC",
            "variant": "on",
            "value": True,
        },
    )


def test_after_calls_debug_with_evaluation_context(hook_context):
    mock_logger = MagicMock()
    hook = LoggingHook(logger=mock_logger, include_evaluation_context=True)
    details = FlagEvaluationDetails(
        flag_key="my-flag",
        value=True,
        variant="on",
        reason="STATIC",
    )
    hook.after(hook_context, details, hints={})

    mock_logger.debug.assert_called_with(
        "After stage %s",
        {
            "stage": "after",
            "flag_key": "my-flag",
            "default_value": False,
            "domain": "my-domain",
            "provider_name": "my-provider",
            "reason": "STATIC",
            "variant": "on",
            "value": True,
            "evaluation_context": {
                "targeting_key": "user-1",
                "attributes": {"env": "prod"},
            },
        },
    )


def test_error_calls_error_log(hook_context):
    mock_logger = MagicMock()
    hook = LoggingHook(logger=mock_logger)
    exception = Exception("something went wrong")
    hook.error(hook_context, exception, hints={})

    mock_logger.error.assert_called_with(
        "Error stage %s",
        {
            "stage": "error",
            "flag_key": "my-flag",
            "default_value": False,
            "domain": "my-domain",
            "provider_name": "my-provider",
            "error_code": ErrorCode.GENERAL,
            "error_message": "something went wrong",
        },
    )


def test_error_extracts_error_code_from_open_feature_error(hook_context):
    mock_logger = MagicMock()
    hook = LoggingHook(logger=mock_logger)
    exception = FlagNotFoundError("flag not found")
    hook.error(hook_context, exception, hints={})

    mock_logger.error.assert_called_with(
        "Error stage %s",
        {
            "stage": "error",
            "flag_key": "my-flag",
            "default_value": False,
            "domain": "my-domain",
            "provider_name": "my-provider",
            "error_code": ErrorCode.FLAG_NOT_FOUND,
            "error_message": str(exception),
        },
    )


def test_build_args_without_metadata():
    hook = LoggingHook()
    ctx = HookContext(
        flag_key="flag",
        flag_type=FlagType.STRING,
        default_value="default",
        evaluation_context=EvaluationContext(None, {}),
        client_metadata=None,
        provider_metadata=None,
    )
    result = hook._build_args(ctx)
    assert result == {
        "flag_key": "flag",
        "default_value": "default",
        "domain": None,
        "provider_name": None,
    }


def test_build_args_excludes_evaluation_context_by_default(hook_context):
    hook = LoggingHook()
    result = hook._build_args(hook_context)
    assert result == {
        "flag_key": "my-flag",
        "default_value": False,
        "domain": "my-domain",
        "provider_name": "my-provider",
    }


def test_build_args_includes_evaluation_context_when_enabled(hook_context):
    hook = LoggingHook(include_evaluation_context=True)
    result = hook._build_args(hook_context)
    assert result == {
        "flag_key": "my-flag",
        "default_value": False,
        "domain": "my-domain",
        "provider_name": "my-provider",
        "evaluation_context": {
            "targeting_key": "user-1",
            "attributes": {"env": "prod"},
        },
    }

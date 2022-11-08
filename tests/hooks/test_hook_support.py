from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook_context import HookContext
from open_feature.hooks.hook_support import (
    after_all_hooks,
    after_hooks,
    before_hooks,
    error_hooks,
)
from unittest.mock import ANY


def test_error_hooks_run_error_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType(dict())
    # When
    error_hooks(FlagType.BOOLEAN, hook_context, Exception, [mock_hook], hook_hints)
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.error.assert_called_once()
    mock_hook.error.assert_called_with(hook_context, ANY, hook_hints)


def test_before_hooks_run_before_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType(dict())
    # When
    before_hooks(FlagType.BOOLEAN, hook_context, [mock_hook], hook_hints)
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.before.assert_called_once()
    mock_hook.error.assert_called_with(hook_context, hook_hints)


def test_after_hooks_run_after_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    flag_evaluation_details = FlagEvaluationDetails(
        hook_context.flag_key, "val", "unknown"
    )
    hook_hints = MappingProxyType(dict())
    # When
    after_hooks(
        FlagType.BOOLEAN, hook_context, flag_evaluation_details, [mock_hook], hook_hints
    )
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.after.assert_called_once()
    mock_hook.error.assert_called_with(
        hook_context, flag_evaluation_details, hook_hints
    )


def test_finally_after_hooks_run_finally_after_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType(dict())
    # When
    after_all_hooks(FlagType.BOOLEAN, hook_context, [mock_hook], hook_hints)
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.finally_after.assert_called_once()
    mock_hook.error.assert_called_with(hook_context, hook_hints)

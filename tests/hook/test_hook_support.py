from unittest.mock import ANY, MagicMock

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType
from openfeature.hook import Hook, HookContext
from openfeature.hook.hook_support import (
    after_all_hooks,
    after_hooks,
    before_hooks,
    error_hooks,
)
from openfeature.immutable_dict.mapping_proxy_type import MappingProxyType


def test_error_hooks_run_error_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType(dict())
    # When
    error_hooks(FlagType.BOOLEAN, hook_context, Exception, [mock_hook], hook_hints)
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.error.assert_called_once()
    mock_hook.error.assert_called_with(
        hook_context=hook_context, exception=ANY, hints=hook_hints
    )


def test_before_hooks_run_before_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType(dict())
    # When
    before_hooks(FlagType.BOOLEAN, hook_context, [mock_hook], hook_hints)
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.before.assert_called_once()
    mock_hook.before.assert_called_with(hook_context=hook_context, hints=hook_hints)


def test_before_hooks_merges_evaluation_contexts():
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_1 = MagicMock(spec=Hook)
    hook_1.before.return_value = EvaluationContext("foo", {"key_1": "val_1"})
    hook_2 = MagicMock(spec=Hook)
    hook_2.before.return_value = EvaluationContext("bar", {"key_2": "val_2"})
    hook_3 = MagicMock(spec=Hook)
    hook_3.before.return_value = None

    # When
    context = before_hooks(FlagType.BOOLEAN, hook_context, [hook_1, hook_2, hook_3])

    # Then
    assert context == EvaluationContext("bar", {"key_1": "val_1", "key_2": "val_2"})


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
    mock_hook.after.assert_called_with(
        hook_context=hook_context, details=flag_evaluation_details, hints=hook_hints
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
    mock_hook.finally_after.assert_called_with(
        hook_context=hook_context, hints=hook_hints
    )

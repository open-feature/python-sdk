from unittest.mock import ANY, MagicMock

import pytest

from openfeature.client import ClientMetadata
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType
from openfeature.hook import Hook, HookContext
from openfeature.hook._hook_support import (
    after_all_hooks,
    after_hooks,
    before_hooks,
    error_hooks,
)
from openfeature.immutable_dict.mapping_proxy_type import MappingProxyType
from openfeature.provider.metadata import Metadata


def test_hook_context_has_required_and_optional_fields():
    """Requirement

    4.1.1 - Hook context MUST provide: the "flag key", "flag value type", "evaluation context", "default value" and "hook data".
    4.1.2 - The "hook context" SHOULD provide: access to the "client metadata" and the "provider metadata" fields.
    """

    # Given/When
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, EvaluationContext())

    # Then
    assert hasattr(hook_context, "flag_key")
    assert hasattr(hook_context, "flag_type")
    assert hasattr(hook_context, "default_value")
    assert hasattr(hook_context, "evaluation_context")
    assert hasattr(hook_context, "client_metadata")
    assert hasattr(hook_context, "provider_metadata")
    assert hasattr(hook_context, "hook_data")


def test_hook_context_has_immutable_and_mutable_fields():
    """Requirement

    4.1.3 - The "flag key", "flag type", and "default value" properties MUST be immutable.
    4.1.5 - The "hook data" property MUST be mutable.
    4.1.4.1 - The evaluation context MUST be mutable only within the before hook.
    4.2.2.2 - The client "metadata" field in the "hook context" MUST be immutable.
    4.2.2.3 - The provider "metadata" field in the "hook context" MUST be immutable.
    """

    # Given
    hook_context = HookContext(
        "flag_key", FlagType.BOOLEAN, True, EvaluationContext(), ClientMetadata("name")
    )

    # When
    with pytest.raises(AttributeError):
        hook_context.flag_key = "new_key"
    with pytest.raises(AttributeError):
        hook_context.flag_type = FlagType.STRING
    with pytest.raises(AttributeError):
        hook_context.default_value = "new_value"
    with pytest.raises(AttributeError):
        hook_context.client_metadata = ClientMetadata("new_name")
    with pytest.raises(AttributeError):
        hook_context.provider_metadata = Metadata("name")

    hook_context.evaluation_context = EvaluationContext("targeting_key")
    hook_context.hook_data["key"] = "value"

    # Then
    assert hook_context.flag_key == "flag_key"
    assert hook_context.flag_type is FlagType.BOOLEAN
    assert hook_context.default_value is True
    assert hook_context.evaluation_context.targeting_key == "targeting_key"
    assert hook_context.client_metadata.name == "name"
    assert hook_context.provider_metadata is None
    assert hook_context.hook_data == {"key": "value"}


def test_error_hooks_run_error_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType({})
    # When
    error_hooks(FlagType.BOOLEAN, Exception, [(mock_hook, hook_context)], hook_hints)
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.error.assert_called_once()
    mock_hook.error.assert_called_with(
        hook_context=hook_context, exception=ANY, hints=hook_hints
    )


def test_before_hooks_run_before_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    hook_hints = MappingProxyType({})
    # When
    before_hooks(FlagType.BOOLEAN, [(mock_hook, hook_context)], hook_hints)
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
    context = before_hooks(
        FlagType.BOOLEAN,
        [(hook_1, hook_context), (hook_2, hook_context), (hook_3, hook_context)],
    )

    # Then
    assert context == EvaluationContext("bar", {"key_1": "val_1", "key_2": "val_2"})


def test_after_hooks_run_after_method(mock_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    flag_evaluation_details = FlagEvaluationDetails(
        hook_context.flag_key, "val", "unknown"
    )
    hook_hints = MappingProxyType({})
    # When
    after_hooks(
        FlagType.BOOLEAN,
        flag_evaluation_details,
        [(mock_hook, hook_context)],
        hook_hints,
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
    flag_evaluation_details = FlagEvaluationDetails(
        hook_context.flag_key, "val", "unknown"
    )
    hook_hints = MappingProxyType({})
    # When
    after_all_hooks(
        FlagType.BOOLEAN,
        flag_evaluation_details,
        [(mock_hook, hook_context)],
        hook_hints,
    )
    # Then
    mock_hook.supports_flag_value_type.assert_called_once()
    mock_hook.finally_after.assert_called_once()
    mock_hook.finally_after.assert_called_with(
        hook_context=hook_context, details=flag_evaluation_details, hints=hook_hints
    )

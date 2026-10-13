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


def test_before_hooks_propagates_context_to_subsequent_hook():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    hook_context_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    hook_context_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    received_by_hook_b: list[EvaluationContext] = []

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(
        attributes={"from_hook_a": "visible"}
    )

    hook_b = MagicMock(spec=Hook)

    def hook_b_before(hook_context, hints):
        received_by_hook_b.append(hook_context.evaluation_context)
        return None

    hook_b.before.side_effect = hook_b_before

    # When
    before_hooks(
        FlagType.BOOLEAN,
        [(hook_a, hook_context_a), (hook_b, hook_context_b)],
    )

    # Then
    assert len(received_by_hook_b) == 1
    assert received_by_hook_b[0].attributes.get("from_hook_a") == "visible", (
        "Hook B did not receive the evaluation context returned by Hook A"
    )
    assert received_by_hook_b[0].attributes.get("initial") == "present"


def test_before_hooks_accumulates_context_across_three_hooks():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    ctx_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_c = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    received_by_hook_b: list[EvaluationContext] = []
    received_by_hook_c: list[EvaluationContext] = []

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(attributes={"from_a": "A"})

    hook_b = MagicMock(spec=Hook)

    def hook_b_before(hook_context, hints):
        received_by_hook_b.append(hook_context.evaluation_context)
        return EvaluationContext(attributes={"from_b": "B"})

    hook_b.before.side_effect = hook_b_before

    hook_c = MagicMock(spec=Hook)

    def hook_c_before(hook_context, hints):
        received_by_hook_c.append(hook_context.evaluation_context)
        return None

    hook_c.before.side_effect = hook_c_before

    # When
    before_hooks(
        FlagType.BOOLEAN,
        [(hook_a, ctx_a), (hook_b, ctx_b), (hook_c, ctx_c)],
    )

    # Then
    assert received_by_hook_b[0].attributes.get("from_a") == "A", (
        "Hook B did not receive the evaluation context returned by Hook A"
    )
    assert received_by_hook_c[0].attributes.get("from_a") == "A", (
        "Hook C did not receive the evaluation context returned by Hook A"
    )
    assert received_by_hook_c[0].attributes.get("from_b") == "B", (
        "Hook C did not receive the evaluation context returned by Hook B"
    )


def test_before_hooks_later_hook_overrides_earlier_on_conflict():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    ctx_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_c = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    received_by_hook_c: list[EvaluationContext] = []

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(attributes={"shared": "A"})

    hook_b = MagicMock(spec=Hook)
    hook_b.before.return_value = EvaluationContext(attributes={"shared": "B"})

    hook_c = MagicMock(spec=Hook)

    def hook_c_before(hook_context, hints):
        received_by_hook_c.append(hook_context.evaluation_context)
        return None

    hook_c.before.side_effect = hook_c_before

    # When
    before_hooks(
        FlagType.BOOLEAN,
        [(hook_a, ctx_a), (hook_b, ctx_b), (hook_c, ctx_c)],
    )

    # Then
    assert received_by_hook_c[0].attributes.get("shared") == "B", (
        "Later hook (B) result should override earlier hook (A) result for the same attribute"
    )


def test_before_hooks_none_result_does_not_corrupt_accumulated_context():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    ctx_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_c = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    received_by_hook_c: list[EvaluationContext] = []

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(attributes={"from_a": "A"})

    hook_b = MagicMock(spec=Hook)
    hook_b.before.return_value = None

    hook_c = MagicMock(spec=Hook)

    def hook_c_before(hook_context, hints):
        received_by_hook_c.append(hook_context.evaluation_context)
        return None

    hook_c.before.side_effect = hook_c_before

    # When
    before_hooks(
        FlagType.BOOLEAN,
        [(hook_a, ctx_a), (hook_b, ctx_b), (hook_c, ctx_c)],
    )

    # Then
    assert received_by_hook_c[0].attributes.get("from_a") == "A", (
        "Hook C should still see Hook A's context even though Hook B returned None"
    )


def test_before_hooks_finalizes_hook_contexts_for_all_participating_hooks():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    ctx_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(attributes={"from_a": "A"})
    hook_b = MagicMock(spec=Hook)
    hook_b.before.return_value = EvaluationContext(attributes={"from_b": "B"})

    # When
    before_hooks(FlagType.BOOLEAN, [(hook_a, ctx_a), (hook_b, ctx_b)])

    # Then
    expected = {"initial": "present", "from_a": "A", "from_b": "B"}
    assert ctx_a.evaluation_context.attributes == expected
    assert ctx_b.evaluation_context.attributes == expected


def test_before_hooks_finalizes_hook_contexts_on_exception():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    ctx_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_c = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(attributes={"from_a": "A"})
    hook_b = MagicMock(spec=Hook)
    hook_b.before.side_effect = RuntimeError("hook_b error")
    hook_c = MagicMock(spec=Hook)

    # When
    with pytest.raises(RuntimeError, match="hook_b error"):
        before_hooks(
            FlagType.BOOLEAN, [(hook_a, ctx_a), (hook_b, ctx_b), (hook_c, ctx_c)]
        )

    # Then
    expected = {"initial": "present", "from_a": "A"}
    assert hook_c.before.call_count == 0
    assert ctx_a.evaluation_context.attributes == expected
    assert ctx_b.evaluation_context.attributes == expected
    assert ctx_c.evaluation_context.attributes == expected


def test_before_hooks_unsupported_hook_context_is_not_finalized():
    # Given
    initial_context = EvaluationContext(attributes={"initial": "present"})
    ctx_a = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)
    ctx_b = HookContext("flag_key", FlagType.BOOLEAN, True, initial_context)

    hook_a = MagicMock(spec=Hook)
    hook_a.before.return_value = EvaluationContext(attributes={"from_a": "A"})
    hook_b = MagicMock(spec=Hook)
    hook_b.supports_flag_value_type.return_value = False

    # When
    before_hooks(FlagType.BOOLEAN, [(hook_a, ctx_a), (hook_b, ctx_b)])

    # Then
    assert hook_b.before.call_count == 0
    assert ctx_a.evaluation_context.attributes.get("from_a") == "A"
    assert ctx_b.evaluation_context.attributes.get("from_a") is None


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

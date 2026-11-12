import pytest

from openfeature.api import get_client, set_provider_and_wait
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import GeneralError
from openfeature.flag_evaluation import Reason
from openfeature.hook import Hook
from openfeature.provider.no_op_provider import NoOpProvider


class CapturingHook(Hook):
    def __init__(self, return_value=None, raise_in_before=False):
        self.before_context: EvaluationContext | None = None
        self.after_context: EvaluationContext | None = None
        self.error_context: EvaluationContext | None = None
        self.finally_context: EvaluationContext | None = None
        self._return_value = return_value
        self._raise_in_before = raise_in_before

    def before(self, hook_context, hints):
        self.before_context = hook_context.evaluation_context
        if self._raise_in_before:
            raise RuntimeError("before hook failure")
        return self._return_value

    def after(self, hook_context, details, hints):
        self.after_context = hook_context.evaluation_context

    def error(self, hook_context, exception, hints):
        self.error_context = hook_context.evaluation_context

    def finally_after(self, hook_context, details, hints):
        self.finally_context = hook_context.evaluation_context

    @property
    def received_context(self) -> EvaluationContext | None:
        return self.before_context


class UnsupportedHook(CapturingHook):
    def supports_flag_value_type(self, flag_type):
        return False


class ContextCapturingProvider(NoOpProvider):
    def __init__(self):
        self.received_context: EvaluationContext | None = None

    def resolve_boolean_details(self, flag_key, default_value, evaluation_context):
        self.received_context = evaluation_context
        return super().resolve_boolean_details(
            flag_key, default_value, evaluation_context
        )


class FailingProvider(NoOpProvider):
    def resolve_boolean_details(self, flag_key, default_value, evaluation_context):
        raise GeneralError("provider resolution failure")


def test_sync_second_before_hook_receives_context_from_first():
    # Given
    set_provider_and_wait(NoOpProvider())
    client = get_client()

    hook_a = CapturingHook(
        return_value=EvaluationContext(attributes={"from_hook_a": "visible"})
    )
    hook_b = CapturingHook(return_value=None)
    client.add_hooks([hook_a, hook_b])

    # When
    client.get_boolean_value(flag_key="test-flag", default_value=False)

    # Then
    assert hook_b.received_context is not None
    assert hook_b.received_context.attributes.get("from_hook_a") == "visible", (
        "Hook B did not receive the evaluation context returned by Hook A (sync path)"
    )


def test_sync_third_before_hook_receives_accumulated_context():
    # Given
    set_provider_and_wait(NoOpProvider())
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = CapturingHook(return_value=EvaluationContext(attributes={"from_b": "B"}))
    hook_c = CapturingHook(return_value=None)
    client.add_hooks([hook_a, hook_b, hook_c])

    # When
    client.get_boolean_value(flag_key="test-flag", default_value=False)

    # Then
    assert hook_b.received_context.attributes.get("from_a") == "A", (
        "Hook B did not receive the evaluation context returned by Hook A (sync path)"
    )
    assert hook_c.received_context.attributes.get("from_a") == "A", (
        "Hook C did not receive Hook A's context (sync path)"
    )
    assert hook_c.received_context.attributes.get("from_b") == "B", (
        "Hook C did not receive Hook B's context (sync path)"
    )


@pytest.mark.asyncio
async def test_async_second_before_hook_receives_context_from_first():
    # Given
    set_provider_and_wait(NoOpProvider())
    client = get_client()

    hook_a = CapturingHook(
        return_value=EvaluationContext(attributes={"from_hook_a": "visible"})
    )
    hook_b = CapturingHook(return_value=None)
    client.add_hooks([hook_a, hook_b])

    # When
    await client.get_boolean_value_async(flag_key="test-flag", default_value=False)

    # Then
    assert hook_b.received_context is not None
    assert hook_b.received_context.attributes.get("from_hook_a") == "visible", (
        "Hook B did not receive the evaluation context returned by Hook A (async path)"
    )


@pytest.mark.asyncio
async def test_async_third_before_hook_receives_accumulated_context():
    # Given
    set_provider_and_wait(NoOpProvider())
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = CapturingHook(return_value=EvaluationContext(attributes={"from_b": "B"}))
    hook_c = CapturingHook(return_value=None)
    client.add_hooks([hook_a, hook_b, hook_c])

    # When
    await client.get_boolean_value_async(flag_key="test-flag", default_value=False)

    # Then
    assert hook_b.received_context.attributes.get("from_a") == "A", (
        "Hook B did not receive the evaluation context returned by Hook A (async path)"
    )
    assert hook_c.received_context.attributes.get("from_a") == "A", (
        "Hook C did not receive Hook A's context (async path)"
    )
    assert hook_c.received_context.attributes.get("from_b") == "B", (
        "Hook C did not receive Hook B's context (async path)"
    )


def test_lifecycle_hooks_receive_accumulated_context_on_success():
    # Given
    provider = ContextCapturingProvider()
    set_provider_and_wait(provider)
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = CapturingHook(return_value=EvaluationContext(attributes={"from_b": "B"}))
    client.add_hooks([hook_a, hook_b])

    # When
    client.get_boolean_value(
        flag_key="test-flag",
        default_value=False,
        evaluation_context=EvaluationContext(attributes={"initial": "present"}),
    )

    # Then
    expected = {"initial": "present", "from_a": "A", "from_b": "B"}
    assert provider.received_context is not None
    assert provider.received_context.attributes == expected
    for hook in (hook_a, hook_b):
        assert hook.after_context is not None
        assert hook.after_context.attributes == expected
        assert hook.finally_context is not None
        assert hook.finally_context.attributes == expected


def test_lifecycle_hooks_receive_accumulated_context_on_before_failure():
    # Given
    set_provider_and_wait(NoOpProvider())
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = CapturingHook(raise_in_before=True)
    hook_c = CapturingHook(return_value=None)
    client.add_hooks([hook_a, hook_b, hook_c])

    # When
    res = client.get_boolean_value(
        flag_key="test-flag",
        default_value=False,
        evaluation_context=EvaluationContext(attributes={"initial": "present"}),
    )

    # Then
    expected = {"initial": "present", "from_a": "A"}
    assert res is False
    assert hook_c.before_context is None
    for hook in (hook_a, hook_b, hook_c):
        assert hook.error_context is not None
        assert hook.error_context.attributes == expected
        assert hook.finally_context is not None
        assert hook.finally_context.attributes == expected


def test_lifecycle_hooks_receive_accumulated_context_on_provider_failure():
    # Given
    set_provider_and_wait(FailingProvider())
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = CapturingHook(return_value=EvaluationContext(attributes={"from_b": "B"}))
    client.add_hooks([hook_a, hook_b])

    # When
    details = client.get_boolean_details(
        flag_key="test-flag",
        default_value=False,
        evaluation_context=EvaluationContext(attributes={"initial": "present"}),
    )

    # Then
    expected = {"initial": "present", "from_a": "A", "from_b": "B"}
    assert details.reason == Reason.ERROR
    for hook in (hook_a, hook_b):
        assert hook.error_context is not None
        assert hook.error_context.attributes == expected
        assert hook.finally_context is not None
        assert hook.finally_context.attributes == expected


def test_lifecycle_hooks_preserve_merge_precedence_on_conflict():
    # Given
    provider = ContextCapturingProvider()
    set_provider_and_wait(provider)
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"shared": "A"}))
    hook_b = CapturingHook(return_value=EvaluationContext(attributes={"shared": "B"}))
    client.add_hooks([hook_a, hook_b])

    # When
    client.get_boolean_value(
        flag_key="test-flag",
        default_value=False,
        evaluation_context=EvaluationContext(attributes={"shared": "initial"}),
    )

    # Then
    assert hook_b.before_context is not None
    assert hook_b.before_context.attributes.get("shared") == "A"
    assert provider.received_context is not None
    assert provider.received_context.attributes.get("shared") == "B"
    for hook in (hook_a, hook_b):
        assert hook.after_context is not None
        assert hook.after_context.attributes.get("shared") == "B"
        assert hook.finally_context is not None
        assert hook.finally_context.attributes.get("shared") == "B"


def test_lifecycle_hooks_none_return_preserves_accumulated_context():
    # Given
    provider = ContextCapturingProvider()
    set_provider_and_wait(provider)
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = CapturingHook(return_value=None)
    hook_c = CapturingHook(return_value=EvaluationContext(attributes={"from_c": "C"}))
    client.add_hooks([hook_a, hook_b, hook_c])

    # When
    client.get_boolean_value(
        flag_key="test-flag",
        default_value=False,
        evaluation_context=EvaluationContext(attributes={"initial": "present"}),
    )

    # Then
    expected = {"initial": "present", "from_a": "A", "from_c": "C"}
    assert hook_c.before_context is not None
    assert hook_c.before_context.attributes.get("from_a") == "A"
    assert provider.received_context is not None
    assert provider.received_context.attributes == expected
    for hook in (hook_a, hook_b, hook_c):
        assert hook.after_context is not None
        assert hook.after_context.attributes == expected
        assert hook.finally_context is not None
        assert hook.finally_context.attributes == expected


def test_lifecycle_hooks_unsupported_flag_type_context_is_not_finalized():
    # Given
    set_provider_and_wait(NoOpProvider())
    client = get_client()

    hook_a = CapturingHook(return_value=EvaluationContext(attributes={"from_a": "A"}))
    hook_b = UnsupportedHook()
    client.add_hooks([hook_a, hook_b])

    # When
    client.get_boolean_value(
        flag_key="test-flag",
        default_value=False,
        evaluation_context=EvaluationContext(attributes={"initial": "present"}),
    )

    # Then
    assert hook_b.before_context is None
    assert hook_b.after_context is None
    assert hook_b.finally_context is None
    assert hook_a.after_context is not None
    assert hook_a.after_context.attributes.get("from_a") == "A"

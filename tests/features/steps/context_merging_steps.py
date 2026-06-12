from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence

from behave import given, then, when

from openfeature import api
from openfeature.api import set_transaction_context
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, FlagValueType, Reason
from openfeature.hook import Hook, HookContext, HookHints
from openfeature.provider import AbstractProvider, Metadata


class RetrievableContextProvider(AbstractProvider):
    """Stores the last merged evaluation context it was asked to resolve."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.last_context: EvaluationContext | None = None

    def get_metadata(self) -> Metadata:
        return Metadata(name="retrievable-context-provider")

    def get_provider_hooks(self) -> list[Hook]:
        return []

    def _capture(
        self, default_value: FlagValueType, context: EvaluationContext | None
    ) -> FlagResolutionDetails[typing.Any]:
        self.last_context = context
        return FlagResolutionDetails(value=default_value, reason=Reason.STATIC)

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        return self._capture(default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return self._capture(default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return self._capture(default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return self._capture(default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return self._capture(default_value, evaluation_context)


class _BeforeHookContextInjector(Hook):
    def __init__(self, context: EvaluationContext) -> None:
        self._context = context

    def before(
        self, hook_context: HookContext, hints: HookHints
    ) -> EvaluationContext | None:
        return self._context


_LEVELS = {"API", "Transaction", "Client", "Invocation", "Before Hooks"}


def _ensure_state(context: typing.Any) -> None:
    if getattr(context, "_merging_initialized", False):
        return

    provider = RetrievableContextProvider()
    api.set_provider(provider)
    context.provider = provider
    context.client = api.get_client()
    context.invocation_context = EvaluationContext()
    context.before_hook_context = EvaluationContext()
    context._merging_initialized = True


@given("a stable provider with retrievable context is registered")
def step_impl_retrievable_provider(context: typing.Any) -> None:
    context._merging_initialized = False
    _ensure_state(context)


def _add_entry_at_level(
    context: typing.Any, level: str, key: str, value: typing.Any
) -> None:
    if level not in _LEVELS:
        raise ValueError(f"Unknown level: {level!r}")

    new_entry = (
        EvaluationContext(targeting_key=value)
        if key == "targeting_key"
        else EvaluationContext(attributes={key: value})
    )
    if level == "API":
        api.set_evaluation_context(api.get_evaluation_context().merge(new_entry))
    elif level == "Transaction":
        set_transaction_context(api.get_transaction_context().merge(new_entry))
    elif level == "Client":
        context.client.context = context.client.context.merge(new_entry)
    elif level == "Invocation":
        context.invocation_context = context.invocation_context.merge(new_entry)
    elif level == "Before Hooks":
        context.before_hook_context = context.before_hook_context.merge(new_entry)


@given(
    'A context entry with key "{key}" and value "{value}" is added to the '
    '"{level}" level'
)
def step_impl_add_entry(context: typing.Any, key: str, value: str, level: str) -> None:
    _add_entry_at_level(context, level, key, value)


@given("A table with levels of increasing precedence")
def step_impl_levels_table(context: typing.Any) -> None:
    # The feature table is a single-column list of levels. Behave treats the
    # first row as the heading, so recombine heading + body rows.
    levels = [context.table.headings[0]]
    levels.extend(row[0] for row in context.table.rows)
    context.precedence_levels = levels


@given(
    'Context entries for each level from API level down to the "{level}" level, '
    'with key "{key}" and value "{value}"'
)
def step_impl_entries_down_to(
    context: typing.Any, level: str, key: str, value: str
) -> None:
    levels = context.precedence_levels
    if level not in levels:
        raise ValueError(f"Level {level!r} not in precedence table {levels!r}")
    for current_level in levels:
        _add_entry_at_level(context, current_level, key, value)
        if current_level == level:
            break


@when("Some flag was evaluated")
def step_impl_evaluate(context: typing.Any) -> None:
    context.client.add_hooks(
        [(_BeforeHookContextInjector(context.before_hook_context))]
    )
    context.client.get_boolean_details("some-flag", False, context.invocation_context)


@then('The merged context contains an entry with key "{key}" and value "{value}"')
def step_impl_merged_contains(context: typing.Any, key: str, value: str) -> None:
    assert context.provider.last_context is not None, (
        "provider did not receive an evaluation context"
    )
    last_context = context.provider.last_context
    actual_value = (
        last_context.targeting_key
        if key == "targeting_key"
        else last_context.attributes.get(key)
    )
    assert actual_value == value, f"expected {key!r}={value!r}, got {actual_value!r}"

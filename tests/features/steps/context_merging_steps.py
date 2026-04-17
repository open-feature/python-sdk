from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence

from behave import given, then, when

from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, FlagValueType, Reason
from openfeature.hook import Hook, HookContext, HookHints
from openfeature.provider import AbstractProvider, Metadata
from openfeature.transaction_context import (
    ContextVarsTransactionContextPropagator,
    set_transaction_context,
    set_transaction_context_propagator,
)


class RetrievableContextProvider(AbstractProvider):
    """Stores the last merged evaluation context it was asked to resolve."""

    def __init__(self) -> None:
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
    api.clear_providers()
    api.clear_hooks()
    api.set_evaluation_context(EvaluationContext())
    set_transaction_context_propagator(ContextVarsTransactionContextPropagator())
    set_transaction_context(EvaluationContext())

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
    _ensure_state(context)
    if level not in _LEVELS:
        raise ValueError(f"Unknown level: {level!r}")
    if level == "API":
        current = api.get_evaluation_context()
        api.set_evaluation_context(
            EvaluationContext(
                targeting_key=current.targeting_key,
                attributes={**current.attributes, key: value},
            )
        )
    elif level == "Transaction":
        current = api.get_transaction_context()
        set_transaction_context(
            EvaluationContext(
                targeting_key=current.targeting_key,
                attributes={**current.attributes, key: value},
            )
        )
    elif level == "Client":
        current = context.client.context
        context.client.context = EvaluationContext(
            targeting_key=current.targeting_key,
            attributes={**current.attributes, key: value},
        )
    elif level == "Invocation":
        current = context.invocation_context
        context.invocation_context = EvaluationContext(
            targeting_key=current.targeting_key,
            attributes={**current.attributes, key: value},
        )
    elif level == "Before Hooks":
        current = context.before_hook_context
        context.before_hook_context = EvaluationContext(
            targeting_key=current.targeting_key,
            attributes={**current.attributes, key: value},
        )


@given(
    'A context entry with key "{key}" and value "{value}" is added to the '
    '"{level}" level'
)
def step_impl_add_entry(context: typing.Any, key: str, value: str, level: str) -> None:
    _add_entry_at_level(context, level, key, value)


@given("A table with levels of increasing precedence")
def step_impl_levels_table(context: typing.Any) -> None:
    _ensure_state(context)
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
    _ensure_state(context)
    levels = context.precedence_levels
    if level not in levels:
        raise ValueError(f"Level {level!r} not in precedence table {levels!r}")
    for current_level in levels:
        _add_entry_at_level(context, current_level, key, value)
        if current_level == level:
            break


@when("Some flag was evaluated")
def step_impl_evaluate(context: typing.Any) -> None:
    _ensure_state(context)
    hook = _BeforeHookContextInjector(context.before_hook_context)
    context.client.add_hooks([hook])
    try:
        context.client.get_boolean_details(
            "some-flag", False, context.invocation_context
        )
    finally:
        context.client.hooks = [h for h in context.client.hooks if h is not hook]


@then('The merged context contains an entry with key "{key}" and value "{value}"')
def step_impl_merged_contains(context: typing.Any, key: str, value: str) -> None:
    assert context.provider.last_context is not None, (
        "provider did not receive an evaluation context"
    )
    attributes = context.provider.last_context.attributes
    assert key in attributes, f"key {key!r} missing from merged context: {attributes!r}"
    assert attributes[key] == value, (
        f"expected {key!r}={value!r}, got {attributes[key]!r}"
    )

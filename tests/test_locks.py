from __future__ import annotations

import threading
from unittest.mock import Mock

from openfeature import _event_support
from openfeature import api as api_module
from openfeature import hook as hook_module
from openfeature.client import OpenFeatureClient

from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.hook import Hook, add_hooks, clear_hooks, get_hooks
from openfeature.provider import AbstractProvider
from openfeature.provider import _registry
from openfeature.transaction_context import (
    clear_transaction_context_propagator,
    get_transaction_context,
    set_transaction_context_propagator,
)
from openfeature.transaction_context.no_op_transaction_context_propagator import (
    NoOpTransactionContextPropagator,
)


class _StubProvider(AbstractProvider):
    """Minimal concrete provider for use in concurrency tests."""

    def get_metadata(self):
        m = Mock()
        m.name = "stub"
        return m

    def resolve_boolean_details(self, flag_key, default_value, evaluation_context=None):
        return FlagResolutionDetails(value=default_value)

    def resolve_string_details(self, flag_key, default_value, evaluation_context=None):
        return FlagResolutionDetails(value=default_value)

    def resolve_integer_details(self, flag_key, default_value, evaluation_context=None):
        return FlagResolutionDetails(value=default_value)

    def resolve_float_details(self, flag_key, default_value, evaluation_context=None):
        return FlagResolutionDetails(value=default_value)

    def resolve_object_details(self, flag_key, default_value, evaluation_context=None):
        return FlagResolutionDetails(value=default_value)



def test_clear_providers_does_not_fire_handler_against_removed_provider():
    """
    Forced interleaving:
        Clearer    ──► clear_providers() ──► [registry emptied] ──► barrier ──► clear handlers
        Dispatcher ──► barrier ──► dispatch_event(provider, ...)

    Invariant: the handler is never invoked for a provider that is no longer
    present in the registry.
    """
    registry = _registry.provider_registry

    api_module.clear_providers()
    provider = _StubProvider()
    api_module.set_provider(provider)

    fired_against_removed_provider: list[bool] = []

    def handler(details) -> None:
        registered = {
            registry.get_default_provider(),
            *registry._providers.values(),
        }
        if provider not in registered:
            fired_against_removed_provider.append(True)

    api_module.add_handler(ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, handler)

    window = threading.Barrier(2)
    original_clear = _registry.clear_event_handlers

    def clear_event_handlers_in_window() -> None:
        # Reached only after the registry has already been emptied; rendezvous
        # here so the dispatcher enters precisely the providers-gone /
        # handlers-still-present window the old code exposed.
        window.wait(timeout=5.0)
        original_clear()

    errors: list[Exception] = []

    def clearer() -> None:
        try:
            api_module.clear_providers()
        except Exception as e:  # pragma: no cover
            errors.append(e)

    def dispatcher() -> None:
        try:
            window.wait(timeout=5.0)
            registry.dispatch_event(
                provider,
                ProviderEvent.PROVIDER_CONFIGURATION_CHANGED,
                ProviderEventDetails(),
            )
        except Exception as e:  # pragma: no cover
            errors.append(e)

    _registry.clear_event_handlers = clear_event_handlers_in_window
    threads = [threading.Thread(target=clearer), threading.Thread(target=dispatcher)]
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
        assert not [t for t in threads if t.is_alive()], (
            "threads did not complete — possible deadlock"
        )
        assert not errors, f"Exception(s) raised in threads: {errors}"
        assert not fired_against_removed_provider, (
            "event handler fired for a provider already removed from the "
            "registry: clear_providers() exposed the gap between clearing "
            "providers and clearing event handlers"
        )
    finally:
        _registry.clear_event_handlers = original_clear
        api_module.clear_providers()
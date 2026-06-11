"""Tests for isolated OpenFeature API instances (spec section 1.8)."""

import inspect
import time
from unittest.mock import MagicMock

import pytest

from openfeature import api
from openfeature._api import _default_api
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.hook import Hook
from openfeature.isolated import OpenFeatureAPI, create_api
from openfeature.provider import FeatureProvider, Metadata, ProviderStatus
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.transaction_context import ContextVarsTransactionContextPropagator


def wait_for_mock_call(mock: MagicMock, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if mock.call_count:
            return

        time.sleep(0.01)


# --- Spec 1.8.1: Factory returns independent instances ---


def test_create_api_returns_new_instance():
    api1 = create_api()
    api2 = create_api()
    assert api1 is not api2


def test_isolated_instance_is_openfeature_api():
    api_instance = create_api()
    assert isinstance(api_instance, OpenFeatureAPI)


# --- Spec 1.8.2: Same API contract ---


_ISOLATED_API_PUBLIC_METHODS = (
    "add_handler",
    "add_hooks",
    "clear_evaluation_context",
    "clear_hooks",
    "clear_providers",
    "clear_transaction_context_propagator",
    "get_client",
    "get_evaluation_context",
    "get_hooks",
    "get_provider",
    "get_provider_metadata",
    "get_provider_status",
    "get_transaction_context",
    "remove_handler",
    "set_evaluation_context",
    "set_provider",
    "set_provider_and_wait",
    "set_transaction_context",
    "set_transaction_context_propagator",
    "shutdown",
)


def test_isolated_api_provides_full_api_contract():
    """Spec 1.8.2: factory result MUST expose the same contract as the global API."""
    api_instance = create_api()
    reference = OpenFeatureAPI()

    for name in _ISOLATED_API_PUBLIC_METHODS:
        assert hasattr(api_instance, name), f"isolated API missing method: {name}"
        attr = getattr(api_instance, name)
        assert callable(attr), f"isolated API attribute is not callable: {name}"
        actual = inspect.signature(attr)
        expected = inspect.signature(getattr(reference, name))
        assert actual == expected, (
            f"signature mismatch for {name}: {actual} != {expected}"
        )


def test_isolated_api_get_client_returns_working_client():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="test-provider")

    api_instance = create_api()
    api_instance.set_provider(provider)

    client = api_instance.get_client()
    assert client is not None
    assert client.provider is provider


def test_isolated_api_get_client_with_domain():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="domain-provider")

    api_instance = create_api()
    api_instance.set_provider(provider, domain="my-domain")

    client = api_instance.get_client(domain="my-domain")
    assert client.provider is provider


# --- Isolated state: providers ---


def test_isolated_providers_are_independent():
    provider_a = MagicMock(spec=FeatureProvider)
    provider_a.get_metadata.return_value = MagicMock(name="provider-a")
    provider_b = MagicMock(spec=FeatureProvider)
    provider_b.get_metadata.return_value = MagicMock(name="provider-b")

    api1 = create_api()
    api2 = create_api()

    api1.set_provider(provider_a)
    api2.set_provider(provider_b)

    client1 = api1.get_client()
    client2 = api2.get_client()

    assert client1.provider is provider_a
    assert client2.provider is provider_b


def test_isolated_provider_does_not_affect_global():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="isolated-provider")

    api_instance = create_api()
    api_instance.set_provider(provider)

    # Global singleton should still have NoOpProvider
    global_client = api.get_client()
    assert isinstance(global_client.provider, NoOpProvider)


# --- Spec 1.8.4: Provider should not be bound to multiple APIs ---


def test_binding_provider_to_multiple_apis_raises():
    """Spec 1.8.4: provider must not be bound to more than one OpenFeature API.

    Uses a Protocol-only provider (no AbstractProvider subclass) to ensure
    detection works regardless of provider implementation strategy.
    """
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="protocol-provider")

    api1 = create_api()
    api2 = create_api()

    api1.set_provider(provider)

    with pytest.raises(RuntimeError, match="already bound"):
        api2.set_provider(provider)


def test_rebinding_provider_to_same_api_does_not_raise():
    """Re-binding the same provider to the same API (e.g., on a different domain)
    must not trigger the spec 1.8.4 error."""
    provider = NoOpProvider()
    api_instance = create_api()

    api_instance.set_provider(provider, domain="domain-a")
    # second call must not raise
    api_instance.set_provider(provider, domain="domain-b")

    assert api_instance.get_provider("domain-a") is provider
    assert api_instance.get_provider("domain-b") is provider


def test_provider_can_be_rebound_after_being_released():
    """After a provider is released from one API (via clear_providers/shutdown),
    binding it to another API must not raise."""
    provider = NoOpProvider()

    api1 = create_api()
    api1.set_provider(provider)
    api1.shutdown()

    # provider is released; binding to a different API now succeeds
    api2 = create_api()
    api2.set_provider(provider)

    assert api2.get_provider() is provider


def test_set_provider_rejects_non_weak_referenceable_provider():
    """Providers must be weak-referenceable so the SDK can track bindings
    without leaking memory; surfacing this requirement up front (rather than
    silently skipping the spec 1.8.4 check) avoids hard-to-diagnose bugs."""

    # A direct ``object`` subclass with ``__slots__`` and no ``__weakref__``
    # entry; instances are not weak-referenceable. Implements the
    # ``FeatureProvider`` protocol structurally rather than via inheritance
    # (which would inherit ``__weakref__`` from the parent class).
    class NotWeakReferenceable:
        __slots__ = ()

        def attach(self, on_emit):
            pass

        def detach(self):
            pass

        def get_metadata(self):
            return Metadata(name="not-weak-referenceable")

        def get_provider_hooks(self):
            return []

    provider = NotWeakReferenceable()
    api_instance = create_api()

    with pytest.raises(TypeError, match="weak-referenceable"):
        api_instance.set_provider(provider)  # type: ignore[arg-type]


# --- Isolated state: hooks ---


def test_isolated_hooks_are_independent():
    hook_a = MagicMock(spec=Hook)
    hook_b = MagicMock(spec=Hook)

    api1 = create_api()
    api2 = create_api()

    api1.add_hooks([hook_a])
    api2.add_hooks([hook_b])

    assert hook_a in api1.get_hooks()
    assert hook_b not in api1.get_hooks()
    assert hook_b in api2.get_hooks()
    assert hook_a not in api2.get_hooks()


def test_isolated_hooks_do_not_affect_global():
    global_hook = MagicMock(spec=Hook)
    isolated_hook = MagicMock(spec=Hook)

    api.add_hooks([global_hook])

    api_instance = create_api()
    api_instance.add_hooks([isolated_hook])

    assert api.get_hooks() == [global_hook]
    assert api_instance.get_hooks() == [isolated_hook]


def test_clear_hooks_on_isolated_api():
    hook = MagicMock(spec=Hook)

    api_instance = create_api()
    api_instance.add_hooks([hook])
    assert len(api_instance.get_hooks()) == 1

    api_instance.clear_hooks()
    assert len(api_instance.get_hooks()) == 0


# --- Isolated state: evaluation context ---


def test_isolated_evaluation_context_is_independent():
    ctx_a = EvaluationContext(targeting_key="user-a")
    ctx_b = EvaluationContext(targeting_key="user-b")

    api1 = create_api()
    api2 = create_api()

    api1.set_evaluation_context(ctx_a)
    api2.set_evaluation_context(ctx_b)

    assert api1.get_evaluation_context().targeting_key == "user-a"
    assert api2.get_evaluation_context().targeting_key == "user-b"


def test_isolated_evaluation_context_does_not_affect_global():
    api.set_evaluation_context(EvaluationContext(targeting_key="global-user"))

    api_instance = create_api()
    api_instance.set_evaluation_context(
        EvaluationContext(targeting_key="isolated-user")
    )

    assert api.get_evaluation_context().targeting_key == "global-user"
    assert api_instance.get_evaluation_context().targeting_key == "isolated-user"


# --- Isolated state: events ---


def test_isolated_event_handlers_are_independent():
    handler_a = MagicMock()
    handler_b = MagicMock()

    api1 = create_api()
    api2 = create_api()

    provider1 = MagicMock(spec=FeatureProvider)
    provider1.get_metadata.return_value = MagicMock(name="p1")
    provider2 = MagicMock(spec=FeatureProvider)
    provider2.get_metadata.return_value = MagicMock(name="p2")

    api1.set_provider(provider1)
    api2.set_provider(provider2)

    # Register handlers for CONFIGURATION_CHANGED to test dispatch isolation
    api1.add_handler(ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, handler_a)
    api2.add_handler(ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, handler_b)

    # Dispatch event on api1's registry — only handler_a should fire
    api1._provider_registry.dispatch_event(
        provider1,
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED,
        ProviderEventDetails(),
    )

    wait_for_mock_call(handler_a)
    assert handler_a.call_count == 1
    assert handler_b.call_count == 0


def test_isolated_event_handlers_do_not_affect_global():
    handler = MagicMock()

    api_instance = create_api()
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="p")
    api_instance.set_provider(provider)
    api_instance.add_handler(ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, handler)

    # Dispatch on global — isolated handler should NOT fire
    global_provider = MagicMock(spec=FeatureProvider)
    global_provider.get_metadata.return_value = MagicMock(name="gp")
    api.set_provider(global_provider)

    handler.reset_mock()

    _default_api._event_support.run_handlers_for_provider(
        global_provider,
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED,
        ProviderEventDetails(),
    )

    assert handler.call_count == 0


# --- Provider lifecycle on isolated instances ---


def test_isolated_api_initializes_provider():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="init-provider")

    api_instance = create_api()
    api_instance.set_provider(provider)

    provider.initialize.assert_called_once()


def test_isolated_api_shuts_down_provider():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="shutdown-provider")

    api_instance = create_api()
    api_instance.set_provider(provider)
    api_instance.shutdown()

    provider.shutdown.assert_called_once()


def test_isolated_api_clear_providers():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="clear-provider")

    api_instance = create_api()
    api_instance.set_provider(provider)
    api_instance.clear_providers()

    client = api_instance.get_client()
    assert isinstance(client.provider, NoOpProvider)


# --- Provider status on isolated instances ---


def test_isolated_client_provider_status():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="status-provider")

    api_instance = create_api()
    api_instance.set_provider(provider)

    client = api_instance.get_client()
    assert client.get_provider_status() == ProviderStatus.READY


# --- Transaction context on isolated instances ---


def test_isolated_transaction_context_propagator():
    api1 = create_api()
    api2 = create_api()

    api1.set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

    ctx = EvaluationContext(targeting_key="tx-user")
    api1.set_transaction_context(ctx)

    assert api1.get_transaction_context().targeting_key == "tx-user"
    # api2 still uses NoOpTransactionContextPropagator → empty context
    assert api2.get_transaction_context().targeting_key is None


def test_isolated_transaction_context_with_both_using_contextvars():
    """Two APIs with ContextVars propagators must not share state."""
    api1 = create_api()
    api2 = create_api()

    api1.set_transaction_context_propagator(ContextVarsTransactionContextPropagator())
    api2.set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

    api1.set_transaction_context(EvaluationContext(targeting_key="api1-user"))

    assert api1.get_transaction_context().targeting_key == "api1-user"
    assert api2.get_transaction_context().targeting_key is None


# --- Global singleton backward compatibility ---


def test_global_api_still_works():
    provider = MagicMock(spec=FeatureProvider)
    provider.get_metadata.return_value = MagicMock(name="global-provider")

    api.set_provider(provider)
    client = api.get_client()

    assert client.provider is provider
    provider.initialize.assert_called_once()


def test_global_hooks_still_work():
    hook = MagicMock(spec=Hook)

    api.add_hooks([hook])
    assert hook in api.get_hooks()

    api.clear_hooks()
    assert len(api.get_hooks()) == 0


def test_global_evaluation_context_still_works():
    ctx = EvaluationContext(targeting_key="global-user")
    api.set_evaluation_context(ctx)
    assert api.get_evaluation_context().targeting_key == "global-user"

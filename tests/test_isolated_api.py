"""Tests for isolated OpenFeature API instances (spec section 1.8)."""

from unittest.mock import MagicMock

from openfeature import api
from openfeature._event_support import _default_event_support
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.hook import Hook
from openfeature.isolated import OpenFeatureAPI, create_api
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.transaction_context import ContextVarsTransactionContextPropagator

# --- Spec 1.8.1: Factory returns independent instances ---


def test_create_api_returns_new_instance():
    api1 = create_api()
    api2 = create_api()
    assert api1 is not api2


def test_isolated_instance_is_openfeature_api():
    api_instance = create_api()
    assert isinstance(api_instance, OpenFeatureAPI)


# --- Spec 1.8.2: Same API contract ---


def test_isolated_api_provides_full_api_contract():
    api_instance = create_api()

    # Provider management
    assert hasattr(api_instance, "set_provider")
    assert hasattr(api_instance, "get_provider_metadata")
    assert hasattr(api_instance, "clear_providers")
    assert hasattr(api_instance, "shutdown")

    # Client creation
    assert hasattr(api_instance, "get_client")

    # Hooks
    assert hasattr(api_instance, "add_hooks")
    assert hasattr(api_instance, "clear_hooks")
    assert hasattr(api_instance, "get_hooks")

    # Context
    assert hasattr(api_instance, "get_evaluation_context")
    assert hasattr(api_instance, "set_evaluation_context")

    # Events
    assert hasattr(api_instance, "add_handler")
    assert hasattr(api_instance, "remove_handler")

    # Transaction context
    assert hasattr(api_instance, "get_transaction_context")
    assert hasattr(api_instance, "set_transaction_context")
    assert hasattr(api_instance, "set_transaction_context_propagator")


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
    hook = MagicMock(spec=Hook)

    api_instance = create_api()
    api_instance.add_hooks([hook])

    assert hook not in api.get_hooks()


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
    ctx = EvaluationContext(targeting_key="isolated-user")

    api_instance = create_api()
    api_instance.set_evaluation_context(ctx)

    assert api.get_evaluation_context().targeting_key != "isolated-user"


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

    _default_event_support.run_handlers_for_provider(
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

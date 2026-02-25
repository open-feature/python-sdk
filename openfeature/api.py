from openfeature import _event_support
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import (
    get_evaluation_context,
    set_evaluation_context,
)
from openfeature.event import (
    EventHandler,
    ProviderEvent,
)
from openfeature.hook import add_hooks, clear_hooks, get_hooks
from openfeature.provider import FeatureProvider
from openfeature.provider._registry import provider_registry
from openfeature.provider.metadata import Metadata
from openfeature.transaction_context import (
    get_transaction_context,
    set_transaction_context,
    set_transaction_context_propagator,
)

__all__ = [
    "add_handler",
    "add_hooks",
    "clear_hooks",
    "clear_providers",
    "get_client",
    "get_evaluation_context",
    "get_hooks",
    "get_provider_metadata",
    "get_transaction_context",
    "remove_handler",
    "set_evaluation_context",
    "set_provider",
    "set_provider_and_wait",
    "set_transaction_context",
    "set_transaction_context_propagator",
    "shutdown",
]


def get_client(
    domain: str | None = None, version: str | None = None
) -> OpenFeatureClient:
    return OpenFeatureClient(domain=domain, version=version)


def set_provider(provider: FeatureProvider, domain: str | None = None) -> None:
    """Set the provider, calling initialize() synchronously.

    Note: In a future major version, this function should run initialize()
    in a background thread to match the non-blocking semantics of
    set_provider() in the Java, Go, and Node.js SDKs. Callers who need
    blocking behavior should migrate to set_provider_and_wait().
    """
    if domain is None:
        provider_registry.set_default_provider(provider)
    else:
        provider_registry.set_provider(domain, provider)


def set_provider_and_wait(provider: FeatureProvider, domain: str | None = None) -> None:
    """Set the provider and wait for initialization to complete.

    Blocks the calling thread until the provider's initialize() method
    returns successfully or raises an exception. If initialization fails,
    the exception is re-raised to the caller.

    Spec reference: Requirement 1.1.2.4 - "The API SHOULD provide functions
    to set a provider and wait for the initialize function to return or
    abnormally terminate."
    """
    if domain is None:
        provider_registry.set_default_provider_and_wait(provider)
    else:
        provider_registry.set_provider_and_wait(domain, provider)


def clear_providers() -> None:
    provider_registry.clear_providers()
    _event_support.clear()


def get_provider_metadata(domain: str | None = None) -> Metadata:
    return provider_registry.get_provider(domain).get_metadata()


def shutdown() -> None:
    provider_registry.shutdown()


def add_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _event_support.add_global_handler(event, handler)


def remove_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _event_support.remove_global_handler(event, handler)

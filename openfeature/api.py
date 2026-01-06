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
    "set_transaction_context",
    "set_transaction_context_propagator",
    "shutdown",
]


def get_client(
    domain: str | None = None, version: str | None = None
) -> OpenFeatureClient:
    return OpenFeatureClient(domain=domain, version=version)


def set_provider(provider: FeatureProvider, domain: str | None = None) -> None:
    if domain is None:
        provider_registry.set_default_provider(provider)
    else:
        provider_registry.set_provider(domain, provider)


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

from openfeature._api import _default_api
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
    return _default_api.get_client(domain=domain, version=version)


def set_provider(provider: FeatureProvider, domain: str | None = None) -> None:
    _default_api.set_provider(provider, domain)


def clear_providers() -> None:
    _default_api.clear_providers()


def get_provider_metadata(domain: str | None = None) -> Metadata:
    return _default_api.get_provider_metadata(domain)


def shutdown() -> None:
    _default_api.shutdown()


def add_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _default_api.add_handler(event, handler)


def remove_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _default_api.remove_handler(event, handler)

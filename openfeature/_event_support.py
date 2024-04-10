from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List

from openfeature.event import (
    EventDetails,
    EventHandler,
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.provider import FeatureProvider, ProviderStatus

if TYPE_CHECKING:
    from openfeature.client import OpenFeatureClient


_global_handlers: Dict[ProviderEvent, List[EventHandler]] = defaultdict(list)
_client_handlers: Dict[OpenFeatureClient, Dict[ProviderEvent, List[EventHandler]]] = (
    defaultdict(lambda: defaultdict(list))
)


def run_client_handlers(
    client: OpenFeatureClient, event: ProviderEvent, details: EventDetails
) -> None:
    for handler in _client_handlers[client][event]:
        handler(details)


def run_global_handlers(event: ProviderEvent, details: EventDetails) -> None:
    for handler in _global_handlers[event]:
        handler(details)


def add_client_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    handlers = _client_handlers[client][event]
    handlers.append(handler)

    _run_immediate_handler(client, event, handler)


def remove_client_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    handlers = _client_handlers[client][event]
    handlers.remove(handler)


def add_global_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _global_handlers[event].append(handler)

    from openfeature.api import get_client

    _run_immediate_handler(get_client(), event, handler)


def remove_global_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _global_handlers[event].remove(handler)


def run_handlers_for_provider(
    provider: FeatureProvider,
    event: ProviderEvent,
    provider_details: ProviderEventDetails,
) -> None:
    details = EventDetails.from_provider_event_details(
        provider.get_metadata().name, provider_details
    )
    # run the global handlers
    run_global_handlers(event, details)
    # run the handlers for clients associated to this provider
    for client in _client_handlers:
        if client.provider == provider:
            run_client_handlers(client, event, details)


def _run_immediate_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    status_to_event = {
        ProviderStatus.READY: ProviderEvent.PROVIDER_READY,
        ProviderStatus.ERROR: ProviderEvent.PROVIDER_ERROR,
        ProviderStatus.FATAL: ProviderEvent.PROVIDER_ERROR,
        ProviderStatus.STALE: ProviderEvent.PROVIDER_STALE,
    }
    if event == status_to_event.get(client.get_provider_status()):
        handler(EventDetails(provider_name=client.provider.get_metadata().name))


def clear() -> None:
    _global_handlers.clear()
    _client_handlers.clear()

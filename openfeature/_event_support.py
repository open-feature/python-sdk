from __future__ import annotations

import threading
import typing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger

from openfeature.event import (
    EventDetails,
    EventHandler,
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.provider import FeatureProvider, ProviderStatus

if typing.TYPE_CHECKING:
    from openfeature.client import OpenFeatureClient


logger = getLogger("openfeature")
_event_executor = ThreadPoolExecutor(thread_name_prefix="openfeature-event-handler")

_global_lock = threading.RLock()
_global_handlers: dict[ProviderEvent, list[EventHandler]] = defaultdict(list)

_client_lock = threading.RLock()
_client_handlers: dict[OpenFeatureClient, dict[ProviderEvent, list[EventHandler]]] = (
    defaultdict(lambda: defaultdict(list))
)


def run_client_handlers(
    client: OpenFeatureClient, event: ProviderEvent, details: EventDetails
) -> None:
    with _client_lock:
        handlers_by_event = _client_handlers.get(client)
        if handlers_by_event is None:
            return

        handlers = tuple(handlers_by_event.get(event, ()))

    for handler in handlers:
        _submit_handler(handler, details)


def run_global_handlers(event: ProviderEvent, details: EventDetails) -> None:
    with _global_lock:
        handlers = tuple(_global_handlers.get(event, ()))

    for handler in handlers:
        _submit_handler(handler, details)


def add_client_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    with _client_lock:
        handlers = _client_handlers[client][event]
        handlers.append(handler)

    _run_immediate_handler(client, event, handler)


def remove_client_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    with _client_lock:
        handlers = _client_handlers[client][event]
        handlers.remove(handler)


def add_global_handler(event: ProviderEvent, handler: EventHandler) -> None:
    with _global_lock:
        _global_handlers[event].append(handler)

    from openfeature.api import get_client  # noqa: PLC0415

    _run_immediate_handler(get_client(), event, handler)


def remove_global_handler(event: ProviderEvent, handler: EventHandler) -> None:
    with _global_lock:
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
    with _client_lock:
        clients = tuple(
            client for client in _client_handlers if client.provider == provider
        )

    for client in clients:
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
        _submit_handler(
            handler, EventDetails(provider_name=client.provider.get_metadata().name)
        )


def _submit_handler(handler: EventHandler, details: EventDetails) -> None:
    _event_executor.submit(_run_handler, handler, details)


def _run_handler(handler: EventHandler, details: EventDetails) -> None:
    try:
        handler(details)
    except Exception:
        logger.exception("Unhandled exception in OpenFeature event handler")


def clear() -> None:
    with _global_lock:
        _global_handlers.clear()
    with _client_lock:
        _client_handlers.clear()

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


_logger = getLogger(__name__)

_global_lock = threading.RLock()
_global_handlers: dict[ProviderEvent, list[EventHandler]] = defaultdict(list)

_client_lock = threading.RLock()
_client_handlers: dict[OpenFeatureClient, dict[ProviderEvent, list[EventHandler]]] = (
    defaultdict(lambda: defaultdict(list))
)

_executor_lock = threading.RLock()
_handler_executor = ThreadPoolExecutor(thread_name_prefix="openfeature-event-handler")


def _run_handler(handler: EventHandler, details: EventDetails) -> None:
    try:
        handler(details)
    except Exception:
        _logger.exception("OpenFeature event handler raised an exception")


def _submit_handler(handler: EventHandler, details: EventDetails) -> None:
    with _executor_lock:
        _handler_executor.submit(_run_handler, handler, details)


def _run_handlers(handlers: list[EventHandler], details: EventDetails) -> None:
    for handler in handlers:
        _submit_handler(handler, details)


def run_client_handlers(
    client: OpenFeatureClient, event: ProviderEvent, details: EventDetails
) -> None:
    with _client_lock:
        handlers = list(_client_handlers[client][event])
    _run_handlers(handlers, details)


def run_global_handlers(event: ProviderEvent, details: EventDetails) -> None:
    with _global_lock:
        handlers = list(_global_handlers[event])
    _run_handlers(handlers, details)


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
        client_handlers_snapshot = [
            (client, list(event_handlers[event]))
            for client, event_handlers in _client_handlers.items()
        ]
    handlers = [
        handler
        for client, event_list in client_handlers_snapshot
        if client.provider == provider
        for handler in event_list
    ]
    _run_handlers(handlers, details)


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
            handler,
            EventDetails(provider_name=client.provider.get_metadata().name),
        )


def clear() -> None:
    global _handler_executor
    with _global_lock:
        _global_handlers.clear()
    with _client_lock:
        _client_handlers.clear()
    with _executor_lock:
        old_executor = _handler_executor
        _handler_executor = ThreadPoolExecutor(
            thread_name_prefix="openfeature-event-handler"
        )
    old_executor.shutdown(wait=True, cancel_futures=False)

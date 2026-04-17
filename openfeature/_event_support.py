from __future__ import annotations

import threading
import typing
from collections import defaultdict
from collections.abc import Callable

from openfeature.event import (
    EventDetails,
    EventHandler,
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.provider import FeatureProvider, ProviderStatus

if typing.TYPE_CHECKING:
    from openfeature.client import OpenFeatureClient


class EventSupport:
    """Per-API-instance event handler storage and dispatch."""

    def __init__(self) -> None:
        self._global_lock = threading.RLock()
        self._global_handlers: dict[ProviderEvent, list[EventHandler]] = defaultdict(
            list
        )

        self._client_lock = threading.RLock()
        self._client_handlers: dict[
            OpenFeatureClient, dict[ProviderEvent, list[EventHandler]]
        ] = defaultdict(lambda: defaultdict(list))

    def run_client_handlers(
        self, client: OpenFeatureClient, event: ProviderEvent, details: EventDetails
    ) -> None:
        with self._client_lock:
            for handler in self._client_handlers[client][event]:
                handler(details)

    def run_global_handlers(self, event: ProviderEvent, details: EventDetails) -> None:
        with self._global_lock:
            for handler in self._global_handlers[event]:
                handler(details)

    def add_client_handler(
        self, client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
    ) -> None:
        with self._client_lock:
            handlers = self._client_handlers[client][event]
            handlers.append(handler)

        self._run_immediate_handler(client, event, handler)

    def remove_client_handler(
        self, client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
    ) -> None:
        with self._client_lock:
            handlers = self._client_handlers[client][event]
            handlers.remove(handler)

    def add_global_handler(
        self,
        event: ProviderEvent,
        handler: EventHandler,
        get_client: Callable[[], OpenFeatureClient],
    ) -> None:
        with self._global_lock:
            self._global_handlers[event].append(handler)

        self._run_immediate_handler(get_client(), event, handler)

    def remove_global_handler(
        self, event: ProviderEvent, handler: EventHandler
    ) -> None:
        with self._global_lock:
            self._global_handlers[event].remove(handler)

    def run_handlers_for_provider(
        self,
        provider: FeatureProvider,
        event: ProviderEvent,
        provider_details: ProviderEventDetails,
    ) -> None:
        details = EventDetails.from_provider_event_details(
            provider.get_metadata().name, provider_details
        )
        self.run_global_handlers(event, details)
        with self._client_lock:
            for client in self._client_handlers:
                if client.provider == provider:
                    self.run_client_handlers(client, event, details)

    def _run_immediate_handler(
        self, client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
    ) -> None:
        status_to_event = {
            ProviderStatus.READY: ProviderEvent.PROVIDER_READY,
            ProviderStatus.ERROR: ProviderEvent.PROVIDER_ERROR,
            ProviderStatus.FATAL: ProviderEvent.PROVIDER_ERROR,
            ProviderStatus.STALE: ProviderEvent.PROVIDER_STALE,
        }
        if event == status_to_event.get(client.get_provider_status()):
            handler(EventDetails(provider_name=client.provider.get_metadata().name))

    def clear(self) -> None:
        with self._global_lock:
            self._global_handlers.clear()
        with self._client_lock:
            self._client_handlers.clear()


# Default instance used by the global singleton API
_default_event_support = EventSupport()


# Backward-compatible module-level functions delegating to the default instance
def run_client_handlers(
    client: OpenFeatureClient, event: ProviderEvent, details: EventDetails
) -> None:
    _default_event_support.run_client_handlers(client, event, details)


def run_global_handlers(event: ProviderEvent, details: EventDetails) -> None:
    _default_event_support.run_global_handlers(event, details)


def add_client_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    _default_event_support.add_client_handler(client, event, handler)


def remove_client_handler(
    client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
) -> None:
    _default_event_support.remove_client_handler(client, event, handler)


def add_global_handler(event: ProviderEvent, handler: EventHandler) -> None:
    from openfeature.api import get_client  # noqa: PLC0415

    _default_event_support.add_global_handler(event, handler, get_client)


def remove_global_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _default_event_support.remove_global_handler(event, handler)


def run_handlers_for_provider(
    provider: FeatureProvider,
    event: ProviderEvent,
    provider_details: ProviderEventDetails,
) -> None:
    _default_event_support.run_handlers_for_provider(provider, event, provider_details)


def clear() -> None:
    _default_event_support.clear()

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List

from openfeature.event import (
    EventDetails,
    EventHandler,
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.provider import FeatureProvider

if TYPE_CHECKING:
    from openfeature.client import OpenFeatureClient


class EventSupport:
    _global_handlers: Dict[ProviderEvent, List[EventHandler]]
    _client_handlers: Dict[OpenFeatureClient, Dict[ProviderEvent, List[EventHandler]]]

    def __init__(self) -> None:
        self._global_handlers = defaultdict(list)
        self._client_handlers = defaultdict(lambda: defaultdict(list))

    def run_client_handlers(
        self, client: OpenFeatureClient, event: ProviderEvent, details: EventDetails
    ) -> None:
        for handler in self._client_handlers[client][event]:
            handler(details)

    def run_global_handlers(self, event: ProviderEvent, details: EventDetails) -> None:
        for handler in self._global_handlers[event]:
            handler(details)

    def add_client_handler(
        self, client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
    ) -> None:
        handlers = self._client_handlers[client][event]
        handlers.append(handler)

        self._run_immediate_handler(client, event, handler)

    def remove_client_handler(
        self, client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
    ) -> None:
        handlers = self._client_handlers[client][event]
        handlers.remove(handler)

    def add_global_handler(self, event: ProviderEvent, handler: EventHandler) -> None:
        self._global_handlers[event].append(handler)

        from openfeature.api import get_client

        self._run_immediate_handler(get_client(), event, handler)

    def remove_global_handler(
        self, event: ProviderEvent, handler: EventHandler
    ) -> None:
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
        # run the global handlers
        self.run_global_handlers(event, details)
        # run the handlers for clients associated to this provider
        for client in self._client_handlers:
            if client.provider == provider:
                self.run_client_handlers(client, event, details)

    def _run_immediate_handler(
        self, client: OpenFeatureClient, event: ProviderEvent, handler: EventHandler
    ) -> None:
        if event == ProviderEvent.from_provider_status(client.get_provider_status()):
            handler(EventDetails(provider_name=client.provider.get_metadata().name))

    def clear(self) -> None:
        self._global_handlers.clear()
        self._client_handlers.clear()

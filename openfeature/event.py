from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Union

from openfeature.exception import ErrorCode
from openfeature.provider import FeatureProvider, ProviderStatus

if TYPE_CHECKING:
    from openfeature.client import OpenFeatureClient


class ProviderEvent(Enum):
    PROVIDER_READY = "PROVIDER_READY"
    PROVIDER_CONFIGURATION_CHANGED = "PROVIDER_CONFIGURATION_CHANGED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_FATAL = "PROVIDER_FATAL"
    PROVIDER_STALE = "PROVIDER_STALE"


_provider_status_to_event = {
    ProviderStatus.READY: ProviderEvent.PROVIDER_READY,
    ProviderStatus.ERROR: ProviderEvent.PROVIDER_ERROR,
    ProviderStatus.FATAL: ProviderEvent.PROVIDER_FATAL,
    ProviderStatus.STALE: ProviderEvent.PROVIDER_STALE,
}


@dataclass
class ProviderEventDetails:
    flags_changed: Optional[List[str]] = None
    message: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    metadata: Dict[str, Union[bool, str, int, float]] = field(default_factory=dict)


@dataclass
class EventDetails(ProviderEventDetails):
    provider_name: str = ""
    flags_changed: Optional[List[str]] = None
    message: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    metadata: Dict[str, Union[bool, str, int, float]] = field(default_factory=dict)

    @classmethod
    def from_provider_event_details(
        cls, provider_name: str, details: ProviderEventDetails
    ) -> EventDetails:
        return cls(
            provider_name=provider_name,
            flags_changed=details.flags_changed,
            message=details.message,
            error_code=details.error_code,
            metadata=details.metadata,
        )


EventHandler = Callable[[EventDetails], None]


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
        if event == _provider_status_to_event.get(client.get_provider_status()):
            handler(EventDetails(provider_name=client.provider.get_metadata().name))

    def clear(self) -> None:
        self._global_handlers.clear()
        self._client_handlers.clear()

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from openfeature.exception import ErrorCode

__all__ = ["EventDetails", "EventHandler", "ProviderEvent", "ProviderEventDetails"]


class ProviderEvent(Enum):
    PROVIDER_READY = "PROVIDER_READY"
    PROVIDER_CONFIGURATION_CHANGED = "PROVIDER_CONFIGURATION_CHANGED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_STALE = "PROVIDER_STALE"


@dataclass
class ProviderEventDetails:
    flags_changed: list[str] | None = None
    message: str | None = None
    error_code: ErrorCode | None = None
    metadata: dict[str, bool | str | int | float] = field(
        default_factory=dict
    )


@dataclass
class EventDetails(ProviderEventDetails):
    provider_name: str = ""
    flags_changed: list[str] | None = None
    message: str | None = None
    error_code: ErrorCode | None = None
    metadata: dict[str, bool | str | int | float] = field(
        default_factory=dict
    )

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

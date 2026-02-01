from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping, Sequence
import typing

TrackingAttribute = typing.TypeAlias = bool | int | float | str | Sequence["TrackingAttribute"] | Mapping[str, "TrackingAttribute"]

@dataclass
class TrackingEventDetails:
    value: float | None = None
    attributes: TrackingAttribute = field(default_factory=dict)

    def add(self, key: str, value: TrackingAttribute) -> "TrackingEventDetails":
        self.attributes[key] = value
        return self
    
    def get_value(self) -> float:
        return self.value
    
    def get_attributes(self) -> TrackingAttribute:
        return self.attributes
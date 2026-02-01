from __future__ import annotations

from collections.abc import Mapping, Sequence
import typing

TrackingAttribute = typing.TypeAlias = bool | int | float | str | Sequence["TrackingAttribute"] | Mapping[str, "TrackingAttribute"]

class TrackingEventDetails:
    value: float | None
    attributes: TrackingAttribute

    def __init__(self, value: float | None = None, attributes: TrackingAttribute | None = None):
        self.value = value
        self.attributes = attributes or {}

    def add(self, key: str, value: TrackingAttribute) -> "TrackingEventDetails":
        self.attributes[key] = value
        return self

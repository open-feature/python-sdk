from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence

TrackingValue: typing.TypeAlias = (
    bool | int | float | str | Sequence["TrackingValue"] | Mapping[str, "TrackingValue"]
)


class TrackingEventDetails:
    value: float | None
    attributes: dict[str, TrackingValue]

    def __init__(
        self,
        value: float | None = None,
        attributes: dict[str, TrackingValue] | None = None,
    ):
        self.value = value
        self.attributes = attributes or {}

    def add(self, key: str, value: TrackingValue) -> TrackingEventDetails:
        self.attributes[key] = value
        return self

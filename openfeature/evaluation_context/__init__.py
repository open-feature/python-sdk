from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

__all__ = ["EvaluationContext"]

# https://openfeature.dev/specification/sections/evaluation-context#requirement-312
EvaluationContextAttribute: typing.TypeAlias = (
    bool
    | int
    | float
    | str
    | datetime
    | Sequence["EvaluationContextAttribute"]
    | Mapping[str, "EvaluationContextAttribute"]
)


@dataclass
class EvaluationContext:
    targeting_key: str | None = None
    attributes: Mapping[str, EvaluationContextAttribute] = field(default_factory=dict)

    def merge(self, ctx2: EvaluationContext) -> EvaluationContext:
        if not (self and ctx2):
            return self or ctx2

        attributes = {**self.attributes, **ctx2.attributes}
        targeting_key = ctx2.targeting_key or self.targeting_key

        return EvaluationContext(targeting_key=targeting_key, attributes=attributes)

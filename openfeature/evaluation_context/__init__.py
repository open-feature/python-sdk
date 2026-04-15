from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

__all__ = ["EvaluationContext", "get_evaluation_context", "set_evaluation_context"]

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


def get_evaluation_context() -> EvaluationContext:
    from openfeature._api import _default_api  # noqa: PLC0415

    return _default_api.get_evaluation_context()


def set_evaluation_context(evaluation_context: EvaluationContext) -> None:
    from openfeature._api import _default_api  # noqa: PLC0415

    _default_api.set_evaluation_context(evaluation_context)


# Kept for backward compatibility but no longer used; state lives in _default_api.
_evaluation_context = EvaluationContext()

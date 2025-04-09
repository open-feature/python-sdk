from __future__ import annotations

import typing
from dataclasses import dataclass, field

from openfeature.exception import GeneralError

__all__ = ["EvaluationContext", "get_evaluation_context", "set_evaluation_context"]


@dataclass
class EvaluationContext:
    targeting_key: typing.Optional[str] = None
    attributes: dict = field(default_factory=dict)

    def merge(self, ctx2: EvaluationContext) -> EvaluationContext:
        if not (self and ctx2):
            return self or ctx2

        attributes = {**self.attributes, **ctx2.attributes}
        targeting_key = ctx2.targeting_key or self.targeting_key

        return EvaluationContext(targeting_key=targeting_key, attributes=attributes)


def get_evaluation_context() -> EvaluationContext:
    return _evaluation_context


def set_evaluation_context(evaluation_context: EvaluationContext) -> None:
    global _evaluation_context
    if evaluation_context is None:
        raise GeneralError(error_message="No api level evaluation context")
    _evaluation_context = evaluation_context


# need to be at the bottom, because of the definition order
_evaluation_context = EvaluationContext()

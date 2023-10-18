import typing
from dataclasses import dataclass, field


@dataclass
class EvaluationContext:
    targeting_key: typing.Optional[str] = None
    attributes: dict = field(default_factory=dict)

    def merge(self, ctx2: "EvaluationContext") -> "EvaluationContext":
        if not (self and ctx2):
            return self or ctx2

        attributes = {**self.attributes, **ctx2.attributes}
        targeting_key = ctx2.targeting_key or self.targeting_key

        return EvaluationContext(targeting_key=targeting_key, attributes=attributes)

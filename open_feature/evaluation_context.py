import typing


class EvaluationContext:
    def __init__(
        self,
        targeting_key: typing.Optional[str] = None,
        attributes: typing.Optional[dict] = None,
    ):
        self.targeting_key = targeting_key
        self.attributes = attributes or {}

    def merge(self, ctx2: "EvaluationContext") -> "EvaluationContext":
        if not (self and ctx2):
            return self or ctx2

        attributes = {**self.attributes, **ctx2.attributes}
        targeting_key = ctx2.targeting_key or self.targeting_key

        return EvaluationContext(targeting_key=targeting_key, attributes=attributes)

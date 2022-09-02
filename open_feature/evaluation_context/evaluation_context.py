class EvaluationContext:
    def __init__(self, targeting_key: str = None, attributes: dict = None):
        self.targeting_key = targeting_key
        self.attributes = attributes or {}

    def merge(self, ctx2: "EvaluationContext") -> "EvaluationContext":
        if not (self and ctx2):
            return self or ctx2

        self.attributes = {**self.attributes, **ctx2.attributes}
        self.targeting_key = ctx2.targeting_key or self.targeting_key

        return self

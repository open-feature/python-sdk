class EvaluationContext:
    def __init__(self, targeting_key: str = None, attributes: dict = {}):
        self.targeting_key = targeting_key
        self.attributes = attributes

    def merge(
        self, ctx1: "EvaluationContext", ctx2: "EvaluationContext"
    ) -> "EvaluationContext":
        self.attributes = ctx1.attributes.update(ctx2.attributes)
        self.targeting_key = ctx2.targeting_key or ctx1.targeting_key

        return self

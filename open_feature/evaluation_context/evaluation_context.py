import json

class EvaluationContext:
    """
    EvaluationContext contains metadata pertaining to the evaluation context
    of the flag resolution. This is typically handled within providers which
    may need to make requests to external resources.

    To serialize, you can use `str` or `repr` built-ins to generate a string
    representation of JSON, or you can use the `asdict()` method to generate
    a dictionary of the same structure.
    """
    def __init__(self, targeting_key: str = None, attributes: dict = None):
        self.targeting_key = targeting_key
        self.attributes = attributes or {}

    def merge(self, ctx2: "EvaluationContext") -> "EvaluationContext":
        if not (self and ctx2):
            return self or ctx2

        self.attributes = {**self.attributes, **ctx2.attributes}
        self.targeting_key = ctx2.targeting_key or self.targeting_key

        return self

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return json.dumps(self.asdict(), ensure_ascii=False)

    def asdict(self):
        return {**self.attributes, 'targetingKey': self.targeting_key}


import typing
from dataclasses import dataclass

from open_feature.hooks.hook import Hook


@dataclass
class FlagEvaluationOptions:
    hooks: typing.List[Hook]
    hook_hints: dict

    def __init__(self):
        self.hooks = []
        self.hook_hints = {}

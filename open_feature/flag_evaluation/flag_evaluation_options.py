from dataclasses import dataclass, field
from typing import List

from open_feature.hooks.hook import Hook


@dataclass
class FlagEvaluationOptions:
    hooks: List[Hook] = field(default_factory=list)
    hook_hints: dict = field(default_factory=dict)

    def __init__(self):
        self.hooks = []
        self.hook_hints = {}

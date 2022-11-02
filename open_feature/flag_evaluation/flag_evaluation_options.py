from dataclasses import dataclass, field

from open_feature.hooks.hook import Hook


@dataclass
class FlagEvaluationOptions:
    hooks: list[Hook] = field(default_factory=list)
    hook_hints: dict = field(default_factory=dict)

import typing
from dataclasses import dataclass, field

from open_feature.hooks import Hook


@dataclass
class FlagEvaluationOptions:
    hooks: typing.List[Hook] = field(default_factory=list)
    hook_hints: dict = field(default_factory=dict)

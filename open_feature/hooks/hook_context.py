import typing
from dataclasses import dataclass

from open_feature.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_type import FlagType


@dataclass
class HookContext:
    flag_key: str
    flag_type: FlagType
    default_value: typing.Any
    evaluation_context: EvaluationContext
    client_metadata: typing.Optional[dict] = None
    provider_metadata: typing.Optional[dict] = None

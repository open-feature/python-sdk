import typing
from dataclasses import dataclass, field

from openfeature._backports.strenum import StrEnum
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import FlagNotFoundError
from openfeature.flag_evaluation import FlagMetadata, FlagResolutionDetails, Reason
from openfeature.hook import Hook
from openfeature.provider.metadata import Metadata
from openfeature.provider.provider import AbstractProvider

PASSED_IN_DEFAULT = "Passed in default"


@dataclass
class InMemoryMetadata(Metadata):
    name: str = "In-Memory Provider"


T_co = typing.TypeVar("T_co", covariant=True)


@dataclass(frozen=True)
class InMemoryFlag(typing.Generic[T_co]):
    class State(StrEnum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    default_variant: str
    variants: typing.Dict[str, T_co]
    flag_metadata: FlagMetadata = field(default_factory=dict)
    state: State = State.ENABLED
    context_evaluator: typing.Optional[
        typing.Callable[
            ["InMemoryFlag[T_co]", EvaluationContext], FlagResolutionDetails[T_co]
        ]
    ] = None

    def resolve(
        self, evaluation_context: typing.Optional[EvaluationContext]
    ) -> FlagResolutionDetails[T_co]:
        if self.context_evaluator:
            return self.context_evaluator(
                self, evaluation_context or EvaluationContext()
            )

        return FlagResolutionDetails(
            value=self.variants[self.default_variant],
            reason=Reason.STATIC,
            variant=self.default_variant,
            flag_metadata=self.flag_metadata,
        )


FlagStorage = typing.Dict[str, InMemoryFlag[typing.Any]]

V = typing.TypeVar("V")


class InMemoryProvider(AbstractProvider):
    _flags: FlagStorage

    def __init__(self, flags: FlagStorage) -> None:
        self._flags = flags.copy()

    def get_metadata(self) -> Metadata:
        return InMemoryMetadata()

    def get_provider_hooks(self) -> typing.List[Hook]:
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return self._resolve(flag_key, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return self._resolve(flag_key, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return self._resolve(flag_key, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return self._resolve(flag_key, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[dict, list],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[typing.Union[dict, list]]:
        return self._resolve(flag_key, evaluation_context)

    def _resolve(
        self,
        flag_key: str,
        evaluation_context: typing.Optional[EvaluationContext],
    ) -> FlagResolutionDetails[V]:
        flag = self._flags.get(flag_key)
        if flag is None:
            raise FlagNotFoundError(f"Flag '{flag_key}' not found")
        return flag.resolve(evaluation_context)

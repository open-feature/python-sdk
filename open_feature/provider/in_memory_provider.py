from dataclasses import dataclass
import typing

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.error_code import ErrorCode
from open_feature.flag_evaluation.reason import Reason
from open_feature.flag_evaluation.resolution_details import FlagResolutionDetails
from open_feature.hooks.hook import Hook
from open_feature.provider.metadata import Metadata
from open_feature.provider.provider import AbstractProvider

PASSED_IN_DEFAULT = "Passed in default"


@dataclass
class InMemoryMetadata(Metadata):
    name: str = "In-Memory Provider"


T = typing.TypeVar("T", covariant=True)


@dataclass
class InMemoryFlag(typing.Generic[T]):
    flag_key: str
    default_variant: str
    variants: typing.Dict[str, T]
    reason: typing.Optional[Reason] = Reason.STATIC
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None
    context_evaluator: typing.Optional[
        typing.Callable[["InMemoryFlag", EvaluationContext], FlagResolutionDetails[T]]
    ] = None

    def resolve(
        self, evaluation_context: typing.Optional[EvaluationContext]
    ) -> FlagResolutionDetails[T]:
        if self.context_evaluator:
            return self.context_evaluator(
                self, evaluation_context or EvaluationContext()
            )

        return FlagResolutionDetails(
            value=self.variants[self.default_variant],
            reason=self.reason,
            variant=self.default_variant,
            error_code=self.error_code,
            error_message=self.error_message,
        )


FlagStorage = typing.Dict[str, InMemoryFlag]

V = typing.TypeVar("V")


class InMemoryProvider(AbstractProvider):
    _flags: FlagStorage

    def __init__(self, flags: FlagStorage):
        self._flags = flags

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
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[dict, list],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[typing.Union[dict, list]]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def _resolve(
        self,
        flag_key: str,
        default_value: V,
        evaluation_context: typing.Optional[EvaluationContext],
    ) -> FlagResolutionDetails[V]:
        flag = self._flags.get(flag_key)
        if flag is None:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.FLAG_NOT_FOUND,
                error_message=f"Flag '{flag_key}' not found",
            )
        return flag.resolve(evaluation_context)

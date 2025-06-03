from __future__ import annotations

import typing
from collections.abc import Sequence

from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.provider import AbstractProvider
from openfeature.provider.no_op_metadata import NoOpMetadata

if typing.TYPE_CHECKING:
    from openfeature.evaluation_context import EvaluationContext
    from openfeature.flag_evaluation import FlagValueType
    from openfeature.hook import Hook
    from openfeature.provider import Metadata

PASSED_IN_DEFAULT = "Passed in default"


class NoOpProvider(AbstractProvider):
    def get_metadata(self) -> Metadata:
        return NoOpMetadata()

    def get_provider_hooks(self) -> list[Hook]:
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]:
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

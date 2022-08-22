import typing
from numbers import Number

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.reason import Reason
from open_feature.provider.provider import AbstractProvider

PASSED_IN_DEFAULT = "Passed in default"


class NoOpProvider(AbstractProvider):
    def get_name(self) -> str:
        return "No-op Provider"

    def get_boolean_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: EvaluationContext = EvaluationContext(),
        flag_evaluation_options: typing.Any = None,
    ):
        return FlagEvaluationDetails(
            key=key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def get_string_details(
        self,
        key: str,
        default_value: str,
        evaluation_context: EvaluationContext = EvaluationContext(),
        flag_evaluation_options: typing.Any = None,
    ):
        return FlagEvaluationDetails(
            key=key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def get_number_details(
        self,
        key: str,
        default_value: Number,
        evaluation_context: EvaluationContext = EvaluationContext(),
        flag_evaluation_options: typing.Any = None,
    ):
        return FlagEvaluationDetails(
            key=key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def get_object_details(
        self,
        key: str,
        default_value: dict,
        evaluation_context: EvaluationContext = EvaluationContext(),
        flag_evaluation_options: typing.Any = None,
    ):
        return FlagEvaluationDetails(
            key=key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

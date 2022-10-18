from numbers import Number

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.reason import Reason
from open_feature.provider.metadata import Metadata
from open_feature.provider.provider import AbstractProvider

PASSED_IN_DEFAULT = "Passed in default"


class NoOpProvider(AbstractProvider):
    def get_metadata(self) -> Metadata:
        return Metadata(name="No-op Provider")

    def get_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext = None,
    ):
        return FlagEvaluationDetails(
            flag_key=flag_key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def get_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext = None,
    ):
        return FlagEvaluationDetails(
            flag_key=flag_key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def get_number_details(
        self,
        flag_key: str,
        default_value: Number,
        evaluation_context: EvaluationContext = None,
    ):
        return FlagEvaluationDetails(
            flag_key=flag_key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

    def get_object_details(
        self,
        flag_key: str,
        default_value: dict,
        evaluation_context: EvaluationContext = None,
    ):
        return FlagEvaluationDetails(
            flag_key=flag_key,
            value=default_value,
            reason=Reason.DEFAULT,
            variant=PASSED_IN_DEFAULT,
        )

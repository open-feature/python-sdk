import typing
from numbers import Number

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.exceptions import GeneralError, OpenFeatureError
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.flag_evaluation.reason import Reason
from open_feature.provider.provider import AbstractProvider


class OpenFeatureClient:
    def __init__(
        self,
        name: str,
        version: str,
        context=None,
        hooks: list = None,
        provider: AbstractProvider = None,
    ):
        self.name = name
        self.version = version
        self.context = context
        self.hooks = hooks or []
        self.provider = provider

    def get_boolean_value(
        self,
        key: str,
        default_value: bool,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> bool:
        return self.evaluate_flag_details(
            FlagType.BOOLEAN,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_boolean_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.BOOLEAN,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_string_value(
        self,
        key: str,
        default_value: str,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> str:
        return self.evaluate_flag_details(
            FlagType.STRING,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_string_details(
        self,
        key: str,
        default_value: str,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.STRING,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_number_value(
        self,
        key: str,
        default_value: Number,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> Number:
        return self.evaluate_flag_details(
            FlagType.NUMBER,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_number_details(
        self,
        key: str,
        default_value: Number,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.NUMBER,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_object_value(
        self,
        key: str,
        default_value: dict,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> dict:
        return self.evaluate_flag_details(
            FlagType.OBJECT,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_object_details(
        self,
        key: str,
        default_value: dict,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.OBJECT,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        key: str,
        default_value: typing.Any,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> FlagEvaluationDetails:
        if evaluation_context is None:
            evaluation_context = EvaluationContext()
        try:
            # The merge below will eventually pull in Evaluation contexts from Hooks
            invocation_context = EvaluationContext()
            invocation_context.merge(ctx2=evaluation_context)
            return self.create_provider_evaluation(
                flag_type,
                key,
                default_value,
                invocation_context,
                flag_evaluation_options,
            )
        except OpenFeatureError as ofe:
            return FlagEvaluationDetails(
                key=key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ofe.error_message,
            )

    def create_provider_evaluation(
        self,
        flag_type: FlagType,
        key: str,
        default_value: typing.Any,
        evaluation_context: EvaluationContext = None,
        flag_evaluation_options: typing.Any = None,
    ) -> FlagEvaluationDetails:
        """
        Encapsulated method to create a FlagEvaluationDetail from a specific provider.

        :param flag_type: the type of the flag being returned
        :param key: the string key of the selected flag
        :param default_value: backup value returned if no result found by the provider
        :param evaluation_context: Information for the purposes of flag evaluation
        :param flag_evaluation_options: Additional flag evaluation information
        :return: a FlagEvaluationDetails object with the fully evaluated flag from a
        provider
        """
        args = (
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

        get_details_callable = {
            FlagType.BOOLEAN: self.provider.get_boolean_details,
            FlagType.NUMBER: self.provider.get_number_details,
            FlagType.OBJECT: self.provider.get_object_details,
            FlagType.STRING: self.provider.get_string_details,
        }.get(flag_type)

        if not get_details_callable:
            raise GeneralError(error_message="Unknown flag type")

        return get_details_callable(*args)

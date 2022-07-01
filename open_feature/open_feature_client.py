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
            # The merge below will pull in Evaluation contexts from Hooks
            invocation_context = EvaluationContext.merge(None, evaluation_context)
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
    ):
        args = (
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )
        if flag_type is FlagType.BOOLEAN:
            return self.provider.get_boolean_details(*args)

        elif flag_type is FlagType.NUMBER:
            return self.provider.get_number_details(*args)

        elif flag_type is FlagType.OBJECT:
            return self.provider.get_object_details(*args)
        # Fallback case is a string object
        elif flag_type is FlagType.STRING:
            return self.provider.get_string_details(*args)
        else:
            raise GeneralError(error_message="Unknown flag type")

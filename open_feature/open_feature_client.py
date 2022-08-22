import typing
from numbers import Number

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.exceptions import GeneralError, OpenFeatureError
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.flag_evaluation.reason import Reason
from open_feature.hooks.hook import Hook
from open_feature.hooks.hook_context import HookContext
from open_feature.hooks.hook_support import (
    after_all_hooks,
    after_hooks,
    before_hooks,
    error_hooks,
)
from open_feature.provider.provider import AbstractProvider


class OpenFeatureClient:
    def __init__(
        self,
        name: str,
        version: str,
        context: EvaluationContext = EvaluationContext(),
        hooks: list[Hook] = None,
        provider: AbstractProvider = None,
    ):
        self.name = name
        self.version = version
        self.context = context
        self.hooks = hooks or []
        self.provider = provider

    def add_hooks(self, hooks: list[Hook]):
        self.hooks = self.hooks + hooks

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
        """

        :param flag_type:
        :param key:
        :param default_value:
        :param evaluation_context:
        :param flag_evaluation_options:
        :return:
        """

        if evaluation_context is None:
            evaluation_context = EvaluationContext()

        hook_context = HookContext(
            flag_key=key,
            flag_type=flag_type,
            default_value=default_value,
            evaluation_context=evaluation_context,
            client_metadata=None,
            provider_metadata=None,
        )
        merged_hooks = []

        try:
            invocation_context = before_hooks(
                flag_type, hook_context, merged_hooks, None
            )
            invocation_context.merge(ctx2=evaluation_context)

            merged_context = (
                # Todo pull the evaluation context below from api
                EvaluationContext()
                .merge(self.context)
                .merge(invocation_context)
            )

            flag_evaluation = self.create_provider_evaluation(
                flag_type,
                key,
                default_value,
                merged_context,
                flag_evaluation_options,
            )

            after_hooks(type, hook_context, flag_evaluation, merged_hooks, None)

            return flag_evaluation
        except OpenFeatureError as ofe:
            error_hooks(flag_type, hook_context, merged_hooks, None)
            return FlagEvaluationDetails(
                key=key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ofe.error_message,
            )

        finally:
            after_all_hooks(flag_type, hook_context, merged_hooks, None)

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

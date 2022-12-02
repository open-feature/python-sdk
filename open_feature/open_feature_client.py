import logging
import typing

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.error_code import ErrorCode
from open_feature.exception.exceptions import (
    GeneralError,
    OpenFeatureError,
    TypeMismatchError,
)
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_evaluation_options import FlagEvaluationOptions
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
from open_feature.open_feature_evaluation_context import api_evaluation_context
from open_feature.provider.no_op_provider import NoOpProvider
from open_feature.provider.provider import AbstractProvider

GetDetailCallable = typing.Union[
    typing.Callable[
        [str, bool, typing.Optional[EvaluationContext]], FlagEvaluationDetails[bool]
    ],
    typing.Callable[
        [str, int, typing.Optional[EvaluationContext]], FlagEvaluationDetails[int]
    ],
    typing.Callable[
        [str, float, typing.Optional[EvaluationContext]], FlagEvaluationDetails[float]
    ],
    typing.Callable[
        [str, str, typing.Optional[EvaluationContext]], FlagEvaluationDetails[str]
    ],
    typing.Callable[
        [str, dict, typing.Optional[EvaluationContext]], FlagEvaluationDetails[dict]
    ],
]


class OpenFeatureClient:
    def __init__(
        self,
        name: typing.Optional[str],
        version: typing.Optional[str],
        provider: AbstractProvider,
        context: typing.Optional[EvaluationContext] = None,
        hooks: typing.Optional[typing.List[Hook]] = None,
    ):
        self.name = name
        self.version = version
        self.context = context or EvaluationContext()
        self.hooks = hooks or []
        self.provider = provider

    def add_hooks(self, hooks: typing.List[Hook]):
        self.hooks = self.hooks + hooks

    def get_boolean_value(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> bool:
        return self.evaluate_flag_details(
            FlagType.BOOLEAN,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.BOOLEAN,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_string_value(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> str:
        return self.evaluate_flag_details(
            FlagType.STRING,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.STRING,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_integer_value(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> int:
        return self.get_integer_details(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.INTEGER,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_float_value(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> float:
        return self.get_float_details(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.FLOAT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_object_value(
        self,
        flag_key: str,
        default_value: dict,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> dict:
        return self.evaluate_flag_details(
            FlagType.OBJECT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    def get_object_details(
        self,
        flag_key: str,
        default_value: dict,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails:
        return self.evaluate_flag_details(
            FlagType.OBJECT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: typing.Any,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails:
        """
        Evaluate the flag requested by the user from the clients provider.

        :param flag_type: the type of the flag being returned
        :param flag_key: the string key of the selected flag
        :param default_value: backup value returned if no result found by the provider
        :param evaluation_context: Information for the purposes of flag evaluation
        :param flag_evaluation_options: Additional flag evaluation information
        :return: a FlagEvaluationDetails object with the fully evaluated flag from a
        provider
        """

        if evaluation_context is None:
            evaluation_context = EvaluationContext()

        if flag_evaluation_options is None:
            flag_evaluation_options = FlagEvaluationOptions()

        evaluation_hooks = flag_evaluation_options.hooks
        hook_hints = flag_evaluation_options.hook_hints

        hook_context = HookContext(
            flag_key=flag_key,
            flag_type=flag_type,
            default_value=default_value,
            evaluation_context=evaluation_context,
            client_metadata=None,
            provider_metadata=None,
        )
        # Todo add api level hooks
        # https://github.com/open-feature/spec/blob/main/specification/sections/04-hooks.md#requirement-442
        # Hooks need to be handled in different orders at different stages
        # in the flag evaluation
        # before: API, Client, Invocation, Provider
        merged_hooks = (
            self.hooks + evaluation_hooks + self.provider.get_provider_hooks()
        )
        # after, error, finally: Provider, Invocation, Client, API
        reversed_merged_hooks = merged_hooks[:]
        reversed_merged_hooks.sort()

        try:
            # https://github.com/open-feature/spec/blob/main/specification/sections/03-evaluation-context.md
            # Any resulting evaluation context from a before hook will overwrite
            # duplicate fields defined globally, on the client, or in the invocation.
            # Requirement 3.2.2, 4.3.4: API.context->client.context->invocation.context
            invocation_context = before_hooks(
                flag_type, hook_context, merged_hooks, hook_hints
            )
            invocation_context = invocation_context.merge(ctx2=evaluation_context)

            # Requirement 3.2.2 merge: API.context->client.context->invocation.context
            merged_context = (
                api_evaluation_context().merge(self.context).merge(invocation_context)
            )

            flag_evaluation = self._create_provider_evaluation(
                flag_type,
                flag_key,
                default_value,
                merged_context,
            )

            after_hooks(
                flag_type,
                hook_context,
                flag_evaluation,
                reversed_merged_hooks,
                hook_hints,
            )

            return flag_evaluation

        except OpenFeatureError as err:
            error_hooks(flag_type, hook_context, err, reversed_merged_hooks, hook_hints)

            return FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=err.error_code,
                error_message=err.error_message,
            )
        # Catch any type of exception here since the user can provide any exception
        # in the error hooks
        except Exception as err:  # noqa
            error_hooks(flag_type, hook_context, err, reversed_merged_hooks, hook_hints)

            error_message = getattr(err, "error_message", str(err))
            return FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL,
                error_message=error_message,
            )

        finally:
            after_all_hooks(flag_type, hook_context, reversed_merged_hooks, hook_hints)

    def _create_provider_evaluation(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: typing.Any,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails:
        """
        Encapsulated method to create a FlagEvaluationDetail from a specific provider.

        :param flag_type: the type of the flag being returned
        :param key: the string key of the selected flag
        :param default_value: backup value returned if no result found by the provider
        :param evaluation_context: Information for the purposes of flag evaluation
        :return: a FlagEvaluationDetails object with the fully evaluated flag from a
        provider
        """
        args = (
            flag_key,
            default_value,
            evaluation_context,
        )

        if not self.provider:
            logging.info("No provider configured, using no-op provider.")
            self.provider = NoOpProvider()

        get_details_callables: typing.Mapping[FlagType, GetDetailCallable] = {
            FlagType.BOOLEAN: self.provider.resolve_boolean_details,
            FlagType.INTEGER: self.provider.resolve_integer_details,
            FlagType.FLOAT: self.provider.resolve_float_details,
            FlagType.OBJECT: self.provider.resolve_object_details,
            FlagType.STRING: self.provider.resolve_string_details,
        }

        get_details_callable = get_details_callables.get(flag_type)
        if not get_details_callable:
            raise GeneralError(error_message="Unknown flag type")

        value = get_details_callable(*args)

        if not isinstance(value.value, flag_type.value):
            raise TypeMismatchError()

        return value

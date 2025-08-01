import logging
import typing
from collections.abc import Awaitable, Sequence
from dataclasses import dataclass

from openfeature import _event_support
from openfeature.evaluation_context import EvaluationContext, get_evaluation_context
from openfeature.event import EventHandler, ProviderEvent
from openfeature.exception import (
    ErrorCode,
    GeneralError,
    OpenFeatureError,
    ProviderFatalError,
    ProviderNotReadyError,
    TypeMismatchError,
)
from openfeature.flag_evaluation import (
    FlagEvaluationDetails,
    FlagEvaluationOptions,
    FlagResolutionDetails,
    FlagType,
    FlagValueType,
    Reason,
)
from openfeature.hook import Hook, HookContext, HookHints, get_hooks
from openfeature.hook._hook_support import (
    after_all_hooks,
    after_hooks,
    before_hooks,
    error_hooks,
)
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider._registry import provider_registry
from openfeature.transaction_context import get_transaction_context

__all__ = [
    "ClientMetadata",
    "OpenFeatureClient",
]

logger = logging.getLogger("openfeature")

TypeMap = dict[
    FlagType,
    typing.Union[
        type[bool],
        type[int],
        type[float],
        type[str],
        tuple[type[dict], type[list]],
    ],
]

T = typing.TypeVar("T", bool, int, float, str, typing.Union[dict, list])


class ResolveDetailsCallable(typing.Protocol[T]):
    def __call__(
        self,
        flag_key: str,
        default_value: T,
        evaluation_context: typing.Optional[EvaluationContext],
    ) -> FlagResolutionDetails[T]: ...


class ResolveDetailsCallableAsync(typing.Protocol[T]):
    def __call__(
        self,
        flag_key: str,
        default_value: T,
        evaluation_context: typing.Optional[EvaluationContext],
    ) -> Awaitable[FlagResolutionDetails[T]]: ...


@dataclass
class ClientMetadata:
    name: typing.Optional[str] = None
    domain: typing.Optional[str] = None


class OpenFeatureClient:
    def __init__(
        self,
        domain: typing.Optional[str],
        version: typing.Optional[str],
        context: typing.Optional[EvaluationContext] = None,
        hooks: typing.Optional[list[Hook]] = None,
    ) -> None:
        self.domain = domain
        self.version = version
        self.context = context or EvaluationContext()
        self.hooks = hooks or []

    @property
    def provider(self) -> FeatureProvider:
        return provider_registry.get_provider(self.domain)

    def get_provider_status(self) -> ProviderStatus:
        return provider_registry.get_provider_status(self.provider)

    def get_metadata(self) -> ClientMetadata:
        return ClientMetadata(domain=self.domain)

    def add_hooks(self, hooks: list[Hook]) -> None:
        self.hooks = self.hooks + hooks

    def get_boolean_value(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> bool:
        return self.get_boolean_details(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    async def get_boolean_value_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> bool:
        details = await self.get_boolean_details_async(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )
        return details.value

    def get_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[bool]:
        return self.evaluate_flag_details(
            FlagType.BOOLEAN,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    async def get_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[bool]:
        return await self.evaluate_flag_details_async(
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
        return self.get_string_details(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    async def get_string_value_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> str:
        details = await self.get_string_details_async(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )
        return details.value

    def get_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[str]:
        return self.evaluate_flag_details(
            FlagType.STRING,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    async def get_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[str]:
        return await self.evaluate_flag_details_async(
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

    async def get_integer_value_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> int:
        details = await self.get_integer_details_async(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )
        return details.value

    def get_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[int]:
        return self.evaluate_flag_details(
            FlagType.INTEGER,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    async def get_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[int]:
        return await self.evaluate_flag_details_async(
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

    async def get_float_value_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> float:
        details = await self.get_float_details_async(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )
        return details.value

    def get_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[float]:
        return self.evaluate_flag_details(
            FlagType.FLOAT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    async def get_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[float]:
        return await self.evaluate_flag_details_async(
            FlagType.FLOAT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_object_value(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]:
        return self.get_object_details(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        ).value

    async def get_object_value_async(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]:
        details = await self.get_object_details_async(
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )
        return details.value

    def get_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]:
        return self.evaluate_flag_details(
            FlagType.OBJECT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    async def get_object_details_async(
        self,
        flag_key: str,
        default_value: typing.Union[
            Sequence[FlagValueType], typing.Mapping[str, FlagValueType]
        ],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[
        typing.Union[Sequence[FlagValueType], typing.Mapping[str, FlagValueType]]
    ]:
        return await self.evaluate_flag_details_async(
            FlagType.OBJECT,
            flag_key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def _establish_hooks_and_provider(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: typing.Optional[EvaluationContext],
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions],
    ) -> tuple[
        FeatureProvider,
        HookContext,
        HookHints,
        list[Hook],
        list[Hook],
    ]:
        if evaluation_context is None:
            evaluation_context = EvaluationContext()

        if flag_evaluation_options is None:
            flag_evaluation_options = FlagEvaluationOptions()

        provider = self.provider  # call this once to maintain a consistent reference
        evaluation_hooks = flag_evaluation_options.hooks
        hook_hints = flag_evaluation_options.hook_hints

        # Merge transaction context into evaluation context before creating hook_context
        # This ensures hooks have access to the complete context including transaction context
        merged_eval_context = (
            get_evaluation_context()
            .merge(get_transaction_context())
            .merge(self.context)
            .merge(evaluation_context)
        )

        hook_context = HookContext(
            flag_key=flag_key,
            flag_type=flag_type,
            default_value=default_value,
            evaluation_context=merged_eval_context,
            client_metadata=self.get_metadata(),
            provider_metadata=provider.get_metadata(),
        )
        # Hooks need to be handled in different orders at different stages
        # in the flag evaluation
        # before: API, Client, Invocation, Provider
        merged_hooks = (
            get_hooks() + self.hooks + evaluation_hooks + provider.get_provider_hooks()
        )
        # after, error, finally: Provider, Invocation, Client, API
        reversed_merged_hooks = merged_hooks[:]
        reversed_merged_hooks.reverse()

        return provider, hook_context, hook_hints, merged_hooks, reversed_merged_hooks

    def _assert_provider_status(
        self,
    ) -> typing.Optional[OpenFeatureError]:
        status = self.get_provider_status()
        if status == ProviderStatus.NOT_READY:
            return ProviderNotReadyError()
        if status == ProviderStatus.FATAL:
            return ProviderFatalError()
        return None

    def _run_before_hooks_and_update_context(
        self,
        flag_type: FlagType,
        hook_context: HookContext,
        merged_hooks: list[Hook],
        hook_hints: HookHints,
        evaluation_context: typing.Optional[EvaluationContext],
    ) -> EvaluationContext:
        # https://github.com/open-feature/spec/blob/main/specification/sections/03-evaluation-context.md
        # Any resulting evaluation context from a before hook will overwrite
        # duplicate fields defined globally, on the client, or in the invocation.
        # Requirement 3.2.2, 4.3.4: API.context->client.context->invocation.context
        before_hooks_context = before_hooks(
            flag_type, hook_context, merged_hooks, hook_hints
        )

        # The hook_context.evaluation_context already contains the merged context from
        # _establish_hooks_and_provider, so we just need to merge with the before hooks result
        merged_context = hook_context.evaluation_context.merge(before_hooks_context)

        return merged_context

    @typing.overload
    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[bool]: ...

    @typing.overload
    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[int]: ...

    @typing.overload
    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[float]: ...

    @typing.overload
    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[str]: ...

    @typing.overload
    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: Sequence["FlagValueType"],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[Sequence["FlagValueType"]]: ...

    @typing.overload
    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: typing.Mapping[str, "FlagValueType"],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[typing.Mapping[str, "FlagValueType"]]: ...

    async def evaluate_flag_details_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[FlagValueType]:
        """
        Evaluate the flag requested by the user from the clients provider.

        :param flag_type: the type of the flag being returned
        :param flag_key: the string key of the selected flag
        :param default_value: backup value returned if no result found by the provider
        :param evaluation_context: Information for the purposes of flag evaluation
        :param flag_evaluation_options: Additional flag evaluation information
        :return: a typing.Awaitable[FlagEvaluationDetails] object with the fully evaluated flag from a
        provider
        """
        provider, hook_context, hook_hints, merged_hooks, reversed_merged_hooks = (
            self._establish_hooks_and_provider(
                flag_type,
                flag_key,
                default_value,
                evaluation_context,
                flag_evaluation_options,
            )
        )

        try:
            if provider_err := self._assert_provider_status():
                error_hooks(
                    flag_type,
                    hook_context,
                    provider_err,
                    reversed_merged_hooks,
                    hook_hints,
                )
                flag_evaluation = FlagEvaluationDetails(
                    flag_key=flag_key,
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=provider_err.error_code,
                    error_message=provider_err.error_message,
                )
                return flag_evaluation

            merged_context = self._run_before_hooks_and_update_context(
                flag_type,
                hook_context,
                merged_hooks,
                hook_hints,
                evaluation_context,
            )

            flag_evaluation = await self._create_provider_evaluation_async(
                provider,
                flag_type,
                flag_key,
                default_value,
                merged_context,
            )
            if err := flag_evaluation.get_exception():
                error_hooks(
                    flag_type, hook_context, err, reversed_merged_hooks, hook_hints
                )
                return flag_evaluation

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
            flag_evaluation = FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=err.error_code,
                error_message=err.error_message,
            )
            return flag_evaluation
        # Catch any type of exception here since the user can provide any exception
        # in the error hooks
        except Exception as err:  # pragma: no cover
            logger.exception(
                "Unable to correctly evaluate flag with key: '%s'", flag_key
            )

            error_hooks(flag_type, hook_context, err, reversed_merged_hooks, hook_hints)

            error_message = getattr(err, "error_message", str(err))
            flag_evaluation = FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL,
                error_message=error_message,
            )
            return flag_evaluation

        finally:
            after_all_hooks(
                flag_type,
                hook_context,
                flag_evaluation,
                reversed_merged_hooks,
                hook_hints,
            )

    @typing.overload
    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[bool]: ...

    @typing.overload
    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[int]: ...

    @typing.overload
    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[float]: ...

    @typing.overload
    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[str]: ...

    @typing.overload
    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: Sequence["FlagValueType"],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[Sequence["FlagValueType"]]: ...

    @typing.overload
    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: typing.Mapping[str, "FlagValueType"],
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[typing.Mapping[str, "FlagValueType"]]: ...

    def evaluate_flag_details(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: typing.Optional[EvaluationContext] = None,
        flag_evaluation_options: typing.Optional[FlagEvaluationOptions] = None,
    ) -> FlagEvaluationDetails[FlagValueType]:
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
        provider, hook_context, hook_hints, merged_hooks, reversed_merged_hooks = (
            self._establish_hooks_and_provider(
                flag_type,
                flag_key,
                default_value,
                evaluation_context,
                flag_evaluation_options,
            )
        )

        try:
            if provider_err := self._assert_provider_status():
                error_hooks(
                    flag_type,
                    hook_context,
                    provider_err,
                    reversed_merged_hooks,
                    hook_hints,
                )
                flag_evaluation = FlagEvaluationDetails(
                    flag_key=flag_key,
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=provider_err.error_code,
                    error_message=provider_err.error_message,
                )
                return flag_evaluation

            merged_context = self._run_before_hooks_and_update_context(
                flag_type,
                hook_context,
                merged_hooks,
                hook_hints,
                evaluation_context,
            )

            flag_evaluation = self._create_provider_evaluation(
                provider,
                flag_type,
                flag_key,
                default_value,
                merged_context,
            )
            if err := flag_evaluation.get_exception():
                error_hooks(
                    flag_type, hook_context, err, reversed_merged_hooks, hook_hints
                )
                flag_evaluation.value = default_value
                return flag_evaluation

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

            flag_evaluation = FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=err.error_code,
                error_message=err.error_message,
            )
            return flag_evaluation
        # Catch any type of exception here since the user can provide any exception
        # in the error hooks
        except Exception as err:  # pragma: no cover
            logger.exception(
                "Unable to correctly evaluate flag with key: '%s'", flag_key
            )

            error_hooks(flag_type, hook_context, err, reversed_merged_hooks, hook_hints)

            error_message = getattr(err, "error_message", str(err))
            flag_evaluation = FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL,
                error_message=error_message,
            )
            return flag_evaluation

        finally:
            after_all_hooks(
                flag_type,
                hook_context,
                flag_evaluation,
                reversed_merged_hooks,
                hook_hints,
            )

    async def _create_provider_evaluation_async(
        self,
        provider: FeatureProvider,
        flag_type: FlagType,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[FlagValueType]:
        get_details_callables_async: typing.Mapping[
            FlagType, ResolveDetailsCallableAsync
        ] = {
            FlagType.BOOLEAN: provider.resolve_boolean_details_async,
            FlagType.INTEGER: provider.resolve_integer_details_async,
            FlagType.FLOAT: provider.resolve_float_details_async,
            FlagType.OBJECT: provider.resolve_object_details_async,
            FlagType.STRING: provider.resolve_string_details_async,
        }
        get_details_callable = get_details_callables_async.get(flag_type)
        if not get_details_callable:
            return FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL,
                error_message="Unknown flag type",
            )

        resolution = await get_details_callable(
            flag_key=flag_key,
            default_value=default_value,
            evaluation_context=evaluation_context,
        )
        if resolution.error_code:
            return resolution.to_flag_evaluation_details(flag_key)

        # we need to check the get_args to be compatible with union types.
        if err := _typecheck_flag_value(value=resolution.value, flag_type=flag_type):
            return FlagEvaluationDetails(
                flag_key=flag_key,
                value=resolution.value,
                reason=Reason.ERROR,
                error_code=err.error_code,
                error_message=err.error_message,
            )

        return resolution.to_flag_evaluation_details(flag_key)

    def _create_provider_evaluation(
        self,
        provider: FeatureProvider,
        flag_type: FlagType,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[FlagValueType]:
        """
        Encapsulated method to create a FlagEvaluationDetail from a specific provider.

        :param flag_type: the type of the flag being returned
        :param key: the string key of the selected flag
        :param default_value: backup value returned if no result found by the provider
        :param evaluation_context: Information for the purposes of flag evaluation
        :return: a FlagEvaluationDetails object with the fully evaluated flag from a
        provider
        """
        get_details_callables: typing.Mapping[FlagType, ResolveDetailsCallable] = {
            FlagType.BOOLEAN: provider.resolve_boolean_details,
            FlagType.INTEGER: provider.resolve_integer_details,
            FlagType.FLOAT: provider.resolve_float_details,
            FlagType.OBJECT: provider.resolve_object_details,
            FlagType.STRING: provider.resolve_string_details,
        }

        get_details_callable = get_details_callables.get(flag_type)
        if not get_details_callable:
            return FlagEvaluationDetails(
                flag_key=flag_key,
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL,
                error_message="Unknown flag type",
            )

        resolution = get_details_callable(
            flag_key=flag_key,
            default_value=default_value,
            evaluation_context=evaluation_context,
        )
        if resolution.error_code:
            return resolution.to_flag_evaluation_details(flag_key)

        # we need to check the get_args to be compatible with union types.
        if err := _typecheck_flag_value(value=resolution.value, flag_type=flag_type):
            return FlagEvaluationDetails(
                flag_key=flag_key,
                value=resolution.value,
                reason=Reason.ERROR,
                error_code=err.error_code,
                error_message=err.error_message,
            )

        return resolution.to_flag_evaluation_details(flag_key)

    def add_handler(self, event: ProviderEvent, handler: EventHandler) -> None:
        _event_support.add_client_handler(self, event, handler)

    def remove_handler(self, event: ProviderEvent, handler: EventHandler) -> None:
        _event_support.remove_client_handler(self, event, handler)


def _typecheck_flag_value(
    value: typing.Any, flag_type: FlagType
) -> typing.Optional[OpenFeatureError]:
    type_map: TypeMap = {
        FlagType.BOOLEAN: bool,
        FlagType.STRING: str,
        FlagType.OBJECT: (dict, list),
        FlagType.FLOAT: float,
        FlagType.INTEGER: int,
    }
    _type = type_map.get(flag_type)
    if not _type:
        return GeneralError(error_message="Unknown flag type")
    if not isinstance(value, _type):
        return TypeMismatchError(f"Expected type {_type} but got {type(value)}")
    return None

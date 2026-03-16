from __future__ import annotations

import asyncio
import contextvars
import logging
import threading
import typing
from collections.abc import Awaitable, Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, GeneralError, OpenFeatureError
from openfeature.flag_evaluation import (
    FlagEvaluationDetails,
    FlagResolutionDetails,
    FlagType,
    FlagValueType,
    Reason,
)
from openfeature.hook import Hook, HookContext, HookHints
from openfeature.hook._hook_support import (
    after_all_hooks,
    after_hooks,
    before_hooks,
    error_hooks,
)
from openfeature.provider import (
    AbstractProvider,
    FeatureProvider,
    Metadata,
    ProviderStatus,
)

__all__ = [
    "ComparisonStrategy",
    "EvaluationStrategy",
    "FirstMatchStrategy",
    "FirstSuccessfulStrategy",
    "MultiProvider",
    "ProviderEntry",
]

logger = logging.getLogger("openfeature")

T = typing.TypeVar("T", bound=FlagValueType)
RunMode: typing.TypeAlias = typing.Literal["sequential", "parallel"]
ComparisonMismatchHandler: typing.TypeAlias = Callable[
    [str, Mapping[str, FlagResolutionDetails[FlagValueType]]], None
]


@dataclass(frozen=True)
class ProviderEntry:
    provider: FeatureProvider
    name: str | None = None


@dataclass(frozen=True)
class _ProviderEvaluation(typing.Generic[T]):
    provider_name: str
    provider: FeatureProvider
    result: FlagResolutionDetails[T]


@dataclass(frozen=True)
class _ProviderHookRuntime:
    flag_type: FlagType
    client_metadata: typing.Any
    hook_hints: HookHints


class EvaluationStrategy(typing.Protocol):
    run_mode: RunMode

    def should_use_result(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool: ...

    def should_continue(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool: ...

    def determine_final_result(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluations: list[_ProviderEvaluation[FlagValueType]],
    ) -> FlagResolutionDetails[FlagValueType]: ...


def _is_success(result: FlagResolutionDetails[FlagValueType]) -> bool:
    return result.error_code is None and result.reason != Reason.ERROR


def _validate_run_mode(run_mode: RunMode) -> RunMode:
    if run_mode not in ("sequential", "parallel"):
        raise ValueError(f"Unsupported run_mode '{run_mode}'")
    return run_mode


def _format_result_error(
    provider_name: str, result: FlagResolutionDetails[FlagValueType]
) -> str:
    error_code = (
        result.error_code.value if result.error_code else ErrorCode.GENERAL.value
    )
    error_message = result.error_message or "Unknown error"
    return f"{provider_name}: {error_code} ({error_message})"


def _build_aggregated_error(
    flag_key: str,
    default_value: FlagValueType,
    evaluations: list[_ProviderEvaluation[FlagValueType]],
    prefix: str,
) -> FlagResolutionDetails[FlagValueType]:
    if not evaluations:
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.ERROR,
            error_code=ErrorCode.GENERAL,
            error_message=f"{prefix} for flag '{flag_key}': no providers returned a result",
        )

    errors_text = "; ".join(
        _format_result_error(evaluation.provider_name, evaluation.result)
        for evaluation in evaluations
    )
    return FlagResolutionDetails(
        value=default_value,
        reason=Reason.ERROR,
        error_code=ErrorCode.GENERAL,
        error_message=f"{prefix} for flag '{flag_key}': {errors_text}",
    )


class FirstMatchStrategy:
    def __init__(self, run_mode: RunMode = "sequential") -> None:
        self.run_mode = _validate_run_mode(run_mode)

    def should_use_result(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool:
        del flag_key
        del provider_name
        return _is_success(result)

    def should_continue(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool:
        del flag_key
        del provider_name
        return result.error_code == ErrorCode.FLAG_NOT_FOUND

    def determine_final_result(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluations: list[_ProviderEvaluation[FlagValueType]],
    ) -> FlagResolutionDetails[FlagValueType]:
        for evaluation in evaluations:
            if self.should_use_result(
                flag_key, evaluation.provider_name, evaluation.result
            ):
                return evaluation.result
            if not self.should_continue(
                flag_key, evaluation.provider_name, evaluation.result
            ):
                return evaluation.result
        if evaluations:
            return evaluations[-1].result
        return _build_aggregated_error(
            flag_key,
            default_value,
            evaluations,
            "Multi-provider evaluation failed",
        )


class FirstSuccessfulStrategy:
    def __init__(self, run_mode: RunMode = "sequential") -> None:
        self.run_mode = _validate_run_mode(run_mode)

    def should_use_result(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool:
        del flag_key
        del provider_name
        return _is_success(result)

    def should_continue(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool:
        del flag_key
        del provider_name
        del result
        return True

    def determine_final_result(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluations: list[_ProviderEvaluation[FlagValueType]],
    ) -> FlagResolutionDetails[FlagValueType]:
        for evaluation in evaluations:
            if _is_success(evaluation.result):
                return evaluation.result
        return _build_aggregated_error(
            flag_key,
            default_value,
            evaluations,
            "All providers failed",
        )


class ComparisonStrategy:
    run_mode: RunMode = "parallel"

    def __init__(
        self,
        fallback_provider: str | None = None,
        on_mismatch: ComparisonMismatchHandler | None = None,
    ) -> None:
        self.fallback_provider = fallback_provider
        self.on_mismatch = on_mismatch

    def validate_provider_names(self, provider_names: Sequence[str]) -> None:
        if (
            self.fallback_provider is not None
            and self.fallback_provider not in provider_names
        ):
            raise ValueError(
                f"Fallback provider '{self.fallback_provider}' is not registered"
            )

    def should_use_result(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool:
        del flag_key
        del provider_name
        del result
        return False

    def should_continue(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails[FlagValueType],
    ) -> bool:
        del flag_key
        del provider_name
        del result
        return True

    def determine_final_result(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluations: list[_ProviderEvaluation[FlagValueType]],
    ) -> FlagResolutionDetails[FlagValueType]:
        failed_evaluations = [
            evaluation
            for evaluation in evaluations
            if not _is_success(evaluation.result)
        ]
        if failed_evaluations:
            return _build_aggregated_error(
                flag_key,
                default_value,
                failed_evaluations,
                "Comparison strategy received provider errors",
            )

        # The first provider's result is the "final resolution" (used on agreement).
        # The fallback provider's result is used on mismatch (per JS SDK reference).
        final_evaluation = evaluations[0]
        fallback_evaluation = self._select_fallback_evaluation(evaluations)
        reference_value = final_evaluation.result.value
        has_mismatch = any(
            evaluation.result.value != reference_value for evaluation in evaluations
        )
        if has_mismatch:
            if self.on_mismatch is not None:
                mismatch_results = {
                    evaluation.provider_name: evaluation.result
                    for evaluation in evaluations
                }
                try:
                    self.on_mismatch(flag_key, mismatch_results)
                except Exception:
                    logger.exception(
                        "Comparison strategy mismatch callback failed for flag '%s'",
                        flag_key,
                    )
            return fallback_evaluation.result
        return final_evaluation.result

    def _select_fallback_evaluation(
        self, evaluations: list[_ProviderEvaluation[FlagValueType]]
    ) -> _ProviderEvaluation[FlagValueType]:
        if not evaluations:
            raise ValueError("ComparisonStrategy requires at least one provider")
        if self.fallback_provider is None:
            return evaluations[0]
        for evaluation in evaluations:
            if evaluation.provider_name == self.fallback_provider:
                return evaluation
        raise ValueError(
            f"Fallback provider '{self.fallback_provider}' is not registered"
        )


class MultiProvider(AbstractProvider):
    _status_precedence: tuple[ProviderStatus, ...] = (
        ProviderStatus.FATAL,
        ProviderStatus.NOT_READY,
        ProviderStatus.ERROR,
        ProviderStatus.STALE,
        ProviderStatus.READY,
    )

    _is_internal_hook_provider: typing.ClassVar[bool] = True

    def __init__(
        self,
        providers: list[ProviderEntry],
        strategy: EvaluationStrategy | None = None,
    ) -> None:
        super().__init__()
        if not providers:
            raise ValueError("At least one provider must be provided")

        self.strategy = strategy or FirstMatchStrategy()
        self._registered_providers: list[tuple[str, FeatureProvider]] = []
        self._provider_names: dict[FeatureProvider, str] = {}
        self._provider_statuses: dict[str, ProviderStatus] = {}
        self._aggregate_status = ProviderStatus.NOT_READY
        self._initialized = False
        self._status_lock = threading.Lock()
        self._hook_runtime: contextvars.ContextVar[_ProviderHookRuntime | None] = (
            contextvars.ContextVar(
                f"multi_provider_hook_runtime:{id(self)}",
                default=None,
            )
        )
        self._register_providers(providers)
        self._provider_statuses = {
            provider_name: ProviderStatus.NOT_READY
            for provider_name, _ in self._registered_providers
        }
        validate_provider_names = getattr(
            self.strategy, "validate_provider_names", None
        )
        if callable(validate_provider_names):
            validate_provider_names(
                [provider_name for provider_name, _ in self._registered_providers]
            )

    def uses_internal_provider_hooks(self) -> bool:
        return True

    def set_internal_provider_hook_runtime(
        self,
        flag_type: FlagType,
        client_metadata: typing.Any,
        hook_hints: HookHints,
    ) -> contextvars.Token[_ProviderHookRuntime | None]:
        return self._hook_runtime.set(
            _ProviderHookRuntime(
                flag_type=flag_type,
                client_metadata=client_metadata,
                hook_hints=hook_hints,
            )
        )

    def reset_internal_provider_hook_runtime(
        self, token: contextvars.Token[_ProviderHookRuntime | None]
    ) -> None:
        self._hook_runtime.reset(token)

    def get_status(self) -> ProviderStatus:
        with self._status_lock:
            return self._aggregate_status

    def _register_providers(self, providers: list[ProviderEntry]) -> None:
        name_counts: dict[str, int] = {}
        for entry in providers:
            metadata_name = entry.provider.get_metadata().name or "provider"
            name_counts[metadata_name] = name_counts.get(metadata_name, 0) + 1

        used_names: set[str] = set()
        name_indexes: dict[str, int] = {}

        for entry in providers:
            metadata_name = entry.provider.get_metadata().name or "provider"
            if entry.name:
                if entry.name in used_names:
                    raise ValueError(f"Provider name '{entry.name}' is not unique")
                provider_name = entry.name
            elif name_counts[metadata_name] == 1 and metadata_name not in used_names:
                provider_name = metadata_name
            else:
                while True:
                    name_indexes[metadata_name] = name_indexes.get(metadata_name, 0) + 1
                    provider_name = f"{metadata_name}_{name_indexes[metadata_name]}"
                    if provider_name not in used_names:
                        break

            used_names.add(provider_name)
            self._registered_providers.append((provider_name, entry.provider))
            self._provider_names[entry.provider] = provider_name

    def get_metadata(self) -> Metadata:
        return Metadata(name="MultiProvider")

    def get_provider_hooks(self) -> list[Hook]:
        return []

    def attach(
        self,
        on_emit: Callable[[FeatureProvider, ProviderEvent, ProviderEventDetails], None],
    ) -> None:
        super().attach(on_emit)
        for _, provider in self._registered_providers:
            provider.attach(self._handle_provider_event)

    def detach(self) -> None:
        for _, provider in self._registered_providers:
            provider.detach()
        super().detach()

    def initialize(self, evaluation_context: EvaluationContext) -> None:
        def initialize_provider(
            entry: tuple[str, FeatureProvider],
        ) -> tuple[str, Exception | None]:
            provider_name, provider = entry
            try:
                provider.initialize(evaluation_context)
                return provider_name, None
            except Exception as err:
                return provider_name, err

        with ThreadPoolExecutor(
            max_workers=len(self._registered_providers)
        ) as executor:
            init_results = list(
                executor.map(initialize_provider, self._registered_providers)
            )

        error_messages: list[str] = []
        event_details = ProviderEventDetails()
        for provider_name, err in init_results:
            if err is None:
                self._mark_provider_ready(provider_name)
                continue
            provider_status = self._status_from_exception(err)
            self._set_provider_status(provider_name, provider_status)
            error_messages.append(
                f"Provider '{provider_name}' initialization failed: {self._error_message_from_exception(err)}"
            )
            event_details = self._details_from_exception(err, provider_name)

        self._initialized = True
        self._refresh_aggregate_status(event_details, force=True)

        if error_messages:
            raise GeneralError(
                f"Multi-provider initialization failed: {'; '.join(error_messages)}"
            )

    def shutdown(self) -> None:
        for _, provider in self._registered_providers:
            provider.detach()

        def shutdown_provider(entry: tuple[str, FeatureProvider]) -> None:
            provider_name, provider = entry
            try:
                provider.shutdown()
            except Exception:
                logger.exception("Provider '%s' shutdown failed", provider_name)

        with ThreadPoolExecutor(
            max_workers=len(self._registered_providers)
        ) as executor:
            list(executor.map(shutdown_provider, self._registered_providers))

        with self._status_lock:
            self._provider_statuses = {
                provider_name: ProviderStatus.NOT_READY
                for provider_name, _ in self._registered_providers
            }
            self._aggregate_status = ProviderStatus.NOT_READY

    def _handle_provider_event(
        self,
        provider: FeatureProvider,
        event: ProviderEvent,
        details: ProviderEventDetails,
    ) -> None:
        provider_name = self._provider_names.get(provider)
        if provider_name is None:
            return
        if event == ProviderEvent.PROVIDER_CONFIGURATION_CHANGED:
            self.emit(
                ProviderEvent.PROVIDER_CONFIGURATION_CHANGED,
                self._with_provider_metadata(details, provider_name),
            )
            return
        if event == ProviderEvent.PROVIDER_READY:
            self._set_provider_status(provider_name, ProviderStatus.READY)
        elif event == ProviderEvent.PROVIDER_STALE:
            self._set_provider_status(provider_name, ProviderStatus.STALE)
        elif event == ProviderEvent.PROVIDER_ERROR:
            self._set_provider_status(
                provider_name,
                self._status_from_event_details(details),
            )
        self._refresh_aggregate_status(
            self._with_provider_metadata(details, provider_name)
        )

    def _set_provider_status(
        self, provider_name: str, provider_status: ProviderStatus
    ) -> None:
        with self._status_lock:
            self._provider_statuses[provider_name] = provider_status

    def _mark_provider_ready(self, provider_name: str) -> None:
        with self._status_lock:
            if self._provider_statuses.get(provider_name) == ProviderStatus.NOT_READY:
                self._provider_statuses[provider_name] = ProviderStatus.READY

    def _should_evaluate_provider(self, provider_name: str) -> bool:
        """Check if a provider should be evaluated based on its status.

        Providers with NOT_READY or FATAL status are skipped, matching the
        JS SDK reference behavior (shouldEvaluateThisProvider).

        Before initialize() has been called, all providers are eligible since
        status tracking is not yet meaningful.
        """
        if not self._initialized:
            return True
        with self._status_lock:
            status = self._provider_statuses.get(
                provider_name, ProviderStatus.NOT_READY
            )
        return status not in (ProviderStatus.NOT_READY, ProviderStatus.FATAL)

    def _calculate_aggregate_status(self) -> ProviderStatus:
        statuses = tuple(self._provider_statuses.values())
        if not statuses:
            return ProviderStatus.NOT_READY
        for status in self._status_precedence:
            if status in statuses:
                return status
        return ProviderStatus.NOT_READY

    def _refresh_aggregate_status(
        self,
        details: ProviderEventDetails,
        force: bool = False,
    ) -> None:
        event_to_emit: ProviderEvent | None = None
        event_details = details
        with self._status_lock:
            previous_status = self._aggregate_status
            aggregate_status = self._calculate_aggregate_status()
            if previous_status == aggregate_status and not force:
                return
            self._aggregate_status = aggregate_status
            event_to_emit = self._event_from_status(aggregate_status)
            event_details = self._details_for_status(aggregate_status, details)
        if event_to_emit is not None:
            self.emit(event_to_emit, event_details)

    def _event_from_status(
        self, provider_status: ProviderStatus
    ) -> ProviderEvent | None:
        if provider_status == ProviderStatus.READY:
            return ProviderEvent.PROVIDER_READY
        if provider_status == ProviderStatus.STALE:
            return ProviderEvent.PROVIDER_STALE
        if provider_status in (ProviderStatus.ERROR, ProviderStatus.FATAL):
            return ProviderEvent.PROVIDER_ERROR
        return None

    def _details_for_status(
        self, provider_status: ProviderStatus, details: ProviderEventDetails
    ) -> ProviderEventDetails:
        error_code = details.error_code
        if provider_status == ProviderStatus.FATAL:
            error_code = ErrorCode.PROVIDER_FATAL
        elif provider_status == ProviderStatus.ERROR and error_code is None:
            error_code = ErrorCode.GENERAL
        return ProviderEventDetails(
            flags_changed=details.flags_changed,
            message=details.message,
            error_code=error_code,
            metadata=dict(details.metadata),
        )

    def _with_provider_metadata(
        self, details: ProviderEventDetails, provider_name: str
    ) -> ProviderEventDetails:
        metadata = dict(details.metadata)
        metadata["provider_name"] = provider_name
        return ProviderEventDetails(
            flags_changed=details.flags_changed,
            message=details.message,
            error_code=details.error_code,
            metadata=metadata,
        )

    def _status_from_event_details(
        self, details: ProviderEventDetails
    ) -> ProviderStatus:
        if details.error_code == ErrorCode.PROVIDER_FATAL:
            return ProviderStatus.FATAL
        return ProviderStatus.ERROR

    def _status_from_exception(self, err: Exception) -> ProviderStatus:
        if (
            isinstance(err, OpenFeatureError)
            and err.error_code == ErrorCode.PROVIDER_FATAL
        ):
            return ProviderStatus.FATAL
        return ProviderStatus.ERROR

    def _details_from_exception(
        self, err: Exception, provider_name: str
    ) -> ProviderEventDetails:
        error_code = (
            err.error_code if isinstance(err, OpenFeatureError) else ErrorCode.GENERAL
        )
        error_message = self._error_message_from_exception(err)
        return ProviderEventDetails(
            message=f"Provider '{provider_name}' failed: {error_message}",
            error_code=error_code,
            metadata={"provider_name": provider_name},
        )

    def _error_message_from_exception(self, err: Exception) -> str:
        if isinstance(err, OpenFeatureError) and err.error_message:
            return err.error_message
        return str(err)

    def _resolution_from_exception(
        self, default_value: T, err: Exception
    ) -> FlagResolutionDetails[T]:
        error_code = (
            err.error_code if isinstance(err, OpenFeatureError) else ErrorCode.GENERAL
        )
        error_message = self._error_message_from_exception(err)
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.ERROR,
            error_code=error_code,
            error_message=error_message,
        )

    def _create_provider_hook_contexts(
        self,
        provider: FeatureProvider,
        flag_type: FlagType,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: EvaluationContext,
        client_metadata: typing.Any,
    ) -> list[tuple[Hook, HookContext]]:
        provider_metadata = provider.get_metadata()
        return [
            (
                hook,
                HookContext(
                    flag_key=flag_key,
                    flag_type=flag_type,
                    default_value=default_value,
                    evaluation_context=evaluation_context,
                    client_metadata=client_metadata,
                    provider_metadata=provider_metadata,
                    hook_data={},
                ),
            )
            for hook in provider.get_provider_hooks()
        ]

    def _evaluate_provider_sync(  # noqa: PLR0913
        self,
        provider_name: str,
        provider: FeatureProvider,
        flag_type: FlagType,
        flag_key: str,
        default_value: T,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[
            [FeatureProvider, str, T, EvaluationContext | None],
            FlagResolutionDetails[T],
        ],
    ) -> _ProviderEvaluation[T]:
        runtime = self._hook_runtime.get()
        if runtime is None or not provider.get_provider_hooks():
            try:
                return _ProviderEvaluation(
                    provider_name=provider_name,
                    provider=provider,
                    result=resolve_fn(
                        provider, flag_key, default_value, evaluation_context
                    ),
                )
            except Exception as err:
                return _ProviderEvaluation(
                    provider_name=provider_name,
                    provider=provider,
                    result=self._resolution_from_exception(default_value, err),
                )

        provider_context = evaluation_context or EvaluationContext()
        hook_contexts = self._create_provider_hook_contexts(
            provider,
            flag_type,
            flag_key,
            default_value,
            provider_context,
            runtime.client_metadata,
        )
        reversed_hook_contexts = list(reversed(hook_contexts))
        flag_evaluation = FlagEvaluationDetails(flag_key=flag_key, value=default_value)
        try:
            before_context = before_hooks(flag_type, hook_contexts, runtime.hook_hints)
            resolved_context = provider_context.merge(before_context)
            resolution = resolve_fn(provider, flag_key, default_value, resolved_context)
            flag_evaluation = resolution.to_flag_evaluation_details(flag_key)
            if err := flag_evaluation.get_exception():
                error_hooks(
                    flag_type,
                    err,
                    reversed_hook_contexts,
                    runtime.hook_hints,
                )
                return _ProviderEvaluation(
                    provider_name=provider_name,
                    provider=provider,
                    result=resolution,
                )
            after_hooks(
                flag_type,
                flag_evaluation,
                reversed_hook_contexts,
                runtime.hook_hints,
            )
            return _ProviderEvaluation(
                provider_name=provider_name,
                provider=provider,
                result=resolution,
            )
        except Exception as err:
            error_hooks(
                flag_type,
                err,
                reversed_hook_contexts,
                runtime.hook_hints,
            )
            return _ProviderEvaluation(
                provider_name=provider_name,
                provider=provider,
                result=self._resolution_from_exception(default_value, err),
            )
        finally:
            after_all_hooks(
                flag_type,
                flag_evaluation,
                reversed_hook_contexts,
                runtime.hook_hints,
            )

    async def _evaluate_provider_async(  # noqa: PLR0913
        self,
        provider_name: str,
        provider: FeatureProvider,
        flag_type: FlagType,
        flag_key: str,
        default_value: T,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[
            [FeatureProvider, str, T, EvaluationContext | None],
            Awaitable[FlagResolutionDetails[T]],
        ],
    ) -> _ProviderEvaluation[T]:
        runtime = self._hook_runtime.get()
        if runtime is None or not provider.get_provider_hooks():
            try:
                return _ProviderEvaluation(
                    provider_name=provider_name,
                    provider=provider,
                    result=await resolve_fn(
                        provider, flag_key, default_value, evaluation_context
                    ),
                )
            except Exception as err:
                return _ProviderEvaluation(
                    provider_name=provider_name,
                    provider=provider,
                    result=self._resolution_from_exception(default_value, err),
                )

        provider_context = evaluation_context or EvaluationContext()
        hook_contexts = self._create_provider_hook_contexts(
            provider,
            flag_type,
            flag_key,
            default_value,
            provider_context,
            runtime.client_metadata,
        )
        reversed_hook_contexts = list(reversed(hook_contexts))
        flag_evaluation = FlagEvaluationDetails(flag_key=flag_key, value=default_value)
        try:
            before_context = before_hooks(flag_type, hook_contexts, runtime.hook_hints)
            resolved_context = provider_context.merge(before_context)
            resolution = await resolve_fn(
                provider, flag_key, default_value, resolved_context
            )
            flag_evaluation = resolution.to_flag_evaluation_details(flag_key)
            if err := flag_evaluation.get_exception():
                error_hooks(
                    flag_type,
                    err,
                    reversed_hook_contexts,
                    runtime.hook_hints,
                )
                return _ProviderEvaluation(
                    provider_name=provider_name,
                    provider=provider,
                    result=resolution,
                )
            after_hooks(
                flag_type,
                flag_evaluation,
                reversed_hook_contexts,
                runtime.hook_hints,
            )
            return _ProviderEvaluation(
                provider_name=provider_name,
                provider=provider,
                result=resolution,
            )
        except Exception as err:
            error_hooks(
                flag_type,
                err,
                reversed_hook_contexts,
                runtime.hook_hints,
            )
            return _ProviderEvaluation(
                provider_name=provider_name,
                provider=provider,
                result=self._resolution_from_exception(default_value, err),
            )
        finally:
            after_all_hooks(
                flag_type,
                flag_evaluation,
                reversed_hook_contexts,
                runtime.hook_hints,
            )

    def _evaluate_with_providers(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: T,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[
            [FeatureProvider, str, T, EvaluationContext | None],
            FlagResolutionDetails[T],
        ],
    ) -> FlagResolutionDetails[T]:
        eligible_providers = [
            (name, provider)
            for name, provider in self._registered_providers
            if self._should_evaluate_provider(name)
        ]

        evaluations: list[_ProviderEvaluation[T]] = []

        if self.strategy.run_mode == "parallel":
            # Each worker thread gets its own copy of the current context so
            # that ContextVars (e.g. _hook_runtime) are propagated correctly.
            # ThreadPoolExecutor does not automatically copy context on
            # Python < 3.12, and a single Context.run() is not reentrant.
            with ThreadPoolExecutor(
                max_workers=len(eligible_providers) or 1
            ) as executor:
                futures = [
                    executor.submit(
                        contextvars.copy_context().run,
                        self._evaluate_provider_sync,
                        provider_name,
                        provider,
                        flag_type,
                        flag_key,
                        default_value,
                        evaluation_context,
                        resolve_fn,
                    )
                    for provider_name, provider in eligible_providers
                ]
                evaluations = [future.result() for future in futures]
            return typing.cast(
                FlagResolutionDetails[T],
                self.strategy.determine_final_result(
                    flag_key,
                    default_value,
                    typing.cast(
                        list[_ProviderEvaluation[FlagValueType]],
                        evaluations,
                    ),
                ),
            )

        for provider_name, provider in eligible_providers:
            evaluation = self._evaluate_provider_sync(
                provider_name,
                provider,
                flag_type,
                flag_key,
                default_value,
                evaluation_context,
                resolve_fn,
            )
            evaluations.append(evaluation)
            if self.strategy.should_use_result(
                flag_key,
                provider_name,
                typing.cast(FlagResolutionDetails[FlagValueType], evaluation.result),
            ):
                return evaluation.result
            if not self.strategy.should_continue(
                flag_key,
                provider_name,
                typing.cast(FlagResolutionDetails[FlagValueType], evaluation.result),
            ):
                break

        return typing.cast(
            FlagResolutionDetails[T],
            self.strategy.determine_final_result(
                flag_key,
                default_value,
                typing.cast(
                    list[_ProviderEvaluation[FlagValueType]],
                    evaluations,
                ),
            ),
        )

    async def _evaluate_with_providers_async(
        self,
        flag_type: FlagType,
        flag_key: str,
        default_value: T,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[
            [FeatureProvider, str, T, EvaluationContext | None],
            Awaitable[FlagResolutionDetails[T]],
        ],
    ) -> FlagResolutionDetails[T]:
        eligible_providers = [
            (name, provider)
            for name, provider in self._registered_providers
            if self._should_evaluate_provider(name)
        ]

        evaluations: list[_ProviderEvaluation[T]] = []

        if self.strategy.run_mode == "parallel":
            tasks = [
                asyncio.create_task(
                    self._evaluate_provider_async(
                        provider_name,
                        provider,
                        flag_type,
                        flag_key,
                        default_value,
                        evaluation_context,
                        resolve_fn,
                    )
                )
                for provider_name, provider in eligible_providers
            ]
            evaluations = list(await asyncio.gather(*tasks))
            return typing.cast(
                FlagResolutionDetails[T],
                self.strategy.determine_final_result(
                    flag_key,
                    default_value,
                    typing.cast(
                        list[_ProviderEvaluation[FlagValueType]],
                        evaluations,
                    ),
                ),
            )

        for provider_name, provider in eligible_providers:
            evaluation = await self._evaluate_provider_async(
                provider_name,
                provider,
                flag_type,
                flag_key,
                default_value,
                evaluation_context,
                resolve_fn,
            )
            evaluations.append(evaluation)
            if self.strategy.should_use_result(
                flag_key,
                provider_name,
                typing.cast(FlagResolutionDetails[FlagValueType], evaluation.result),
            ):
                return evaluation.result
            if not self.strategy.should_continue(
                flag_key,
                provider_name,
                typing.cast(FlagResolutionDetails[FlagValueType], evaluation.result),
            ):
                break

        return typing.cast(
            FlagResolutionDetails[T],
            self.strategy.determine_final_result(
                flag_key,
                default_value,
                typing.cast(
                    list[_ProviderEvaluation[FlagValueType]],
                    evaluations,
                ),
            ),
        )

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        return self._evaluate_with_providers(
            FlagType.BOOLEAN,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_boolean_details(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        return await self._evaluate_with_providers_async(
            FlagType.BOOLEAN,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_boolean_details_async(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return self._evaluate_with_providers(
            FlagType.STRING,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_string_details(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    async def resolve_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return await self._evaluate_with_providers_async(
            FlagType.STRING,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_string_details_async(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return self._evaluate_with_providers(
            FlagType.INTEGER,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_integer_details(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    async def resolve_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return await self._evaluate_with_providers_async(
            FlagType.INTEGER,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_integer_details_async(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return self._evaluate_with_providers(
            FlagType.FLOAT,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_float_details(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    async def resolve_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return await self._evaluate_with_providers_async(
            FlagType.FLOAT,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_float_details_async(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return self._evaluate_with_providers(
            FlagType.OBJECT,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_object_details(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

    async def resolve_object_details_async(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return await self._evaluate_with_providers_async(
            FlagType.OBJECT,
            flag_key,
            default_value,
            evaluation_context,
            lambda provider, resolved_flag_key, resolved_default_value, resolved_context: (
                provider.resolve_object_details_async(
                    resolved_flag_key,
                    resolved_default_value,
                    resolved_context,
                )
            ),
        )

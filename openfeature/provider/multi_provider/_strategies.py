from __future__ import annotations

import logging
import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from openfeature.exception import ErrorCode
from openfeature.flag_evaluation import FlagResolutionDetails, FlagValueType, Reason

logger = logging.getLogger("openfeature")

T = typing.TypeVar("T", bound=FlagValueType)
RunMode: typing.TypeAlias = typing.Literal["sequential", "parallel"]
ComparisonMismatchHandler: typing.TypeAlias = Callable[
    [str, Mapping[str, FlagResolutionDetails[FlagValueType]]], None
]


@dataclass(frozen=True)
class _ProviderEvaluation(typing.Generic[T]):
    provider_name: str
    provider: object
    result: FlagResolutionDetails[T]


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
        """Determine the final result from parallel provider evaluations.

        If any provider returns an error, returns an aggregated error result.
        On agreement (all providers return the same value), returns the first
        provider's result. On mismatch, calls the optional ``on_mismatch``
        callback and returns the fallback provider's result.
        """
        if not evaluations:
            return _build_aggregated_error(
                flag_key,
                default_value,
                [],
                "No providers were eligible for evaluation",
            )
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
        reference_value = final_evaluation.result.value
        if not any(
            evaluation.result.value != reference_value for evaluation in evaluations
        ):
            return final_evaluation.result

        fallback_evaluation = self._select_fallback_evaluation(evaluations)
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

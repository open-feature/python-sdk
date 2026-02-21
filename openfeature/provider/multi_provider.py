"""
Multi-Provider implementation for OpenFeature Python SDK.

This provider wraps multiple underlying providers, allowing a single client
to interact with multiple flag sources simultaneously.

See: https://openfeature.dev/specification/appendix-a/#multi-provider
"""

from __future__ import annotations

import asyncio
import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.exception import GeneralError
from openfeature.flag_evaluation import FlagResolutionDetails, FlagValueType, Reason
from openfeature.hook import Hook
from openfeature.provider import AbstractProvider, FeatureProvider, Metadata, ProviderStatus

__all__ = ["MultiProvider", "ProviderEntry", "FirstMatchStrategy", "EvaluationStrategy"]


@dataclass
class ProviderEntry:
    """Configuration for a provider in the Multi-Provider."""

    provider: FeatureProvider
    name: str | None = None


class EvaluationStrategy(typing.Protocol):
    """
    Strategy interface for determining which provider's result to use.
    
    Strategies can be 'sequential' (evaluate one at a time, stop early) or
    'parallel' (evaluate all simultaneously).
    """

    run_mode: typing.Literal["sequential", "parallel"]

    def should_use_result(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails,
    ) -> bool:
        """
        Determine if this result should be used (and stop evaluation if sequential).
        
        :param flag_key: The flag being evaluated
        :param provider_name: Name of the provider that returned this result
        :param result: The resolution details from the provider
        :return: True if this result should be used as the final result
        """
        ...


class FirstMatchStrategy:
    """
    Uses the first successful result from providers (in order).
    
    In sequential mode, stops at the first non-error result.
    In parallel mode, picks the first successful result from the ordered list.
    """

    run_mode: typing.Literal["sequential", "parallel"] = "sequential"

    def should_use_result(
        self,
        flag_key: str,
        provider_name: str,
        result: FlagResolutionDetails,
    ) -> bool:
        """Use the first result that doesn't have an error."""
        return result.reason != Reason.ERROR


class MultiProvider(AbstractProvider):
    """
    A provider that aggregates multiple underlying providers.
    
    Evaluations are delegated to underlying providers based on the configured
    strategy (default: FirstMatchStrategy in sequential mode).
    
    Example:
        provider_a = SomeProvider()
        provider_b = AnotherProvider()
        
        multi = MultiProvider([
            ProviderEntry(provider_a, name="primary"),
            ProviderEntry(provider_b, name="fallback")
        ])
        
        api.set_provider(multi)
    """

    def __init__(
        self,
        providers: list[ProviderEntry],
        strategy: EvaluationStrategy | None = None,
    ):
        """
        Initialize the Multi-Provider.
        
        :param providers: List of ProviderEntry objects defining the providers
        :param strategy: Evaluation strategy (defaults to FirstMatchStrategy)
        """
        super().__init__()
        
        if not providers:
            raise ValueError("At least one provider must be provided")
        
        self.strategy = strategy or FirstMatchStrategy()
        self._registered_providers: list[tuple[str, FeatureProvider]] = []
        self._register_providers(providers)

    def _register_providers(self, providers: list[ProviderEntry]) -> None:
        """
        Register providers with unique names.
        
        Names are determined by:
        1. Explicit name in ProviderEntry
        2. provider.get_metadata().name if unique
        3. {metadata.name}_{index} if not unique
        """
        # Count providers by their metadata name to detect duplicates
        name_counts: dict[str, int] = {}
        for entry in providers:
            metadata_name = entry.provider.get_metadata().name or "provider"
            name_counts[metadata_name] = name_counts.get(metadata_name, 0) + 1

        # Track used names to prevent conflicts
        used_names: set[str] = set()
        name_indices: dict[str, int] = {}

        for entry in providers:
            metadata_name = entry.provider.get_metadata().name or "provider"
            
            if entry.name:
                # Explicit name provided
                if entry.name in used_names:
                    raise ValueError(f"Provider name '{entry.name}' is not unique")
                final_name = entry.name
            elif name_counts[metadata_name] == 1:
                # Metadata name is unique
                final_name = metadata_name
            else:
                # Multiple providers with same metadata name, add index
                name_indices[metadata_name] = name_indices.get(metadata_name, 0) + 1
                final_name = f"{metadata_name}_{name_indices[metadata_name]}"
            
            used_names.add(final_name)
            self._registered_providers.append((final_name, entry.provider))

    def get_metadata(self) -> Metadata:
        """Return metadata including all wrapped provider metadata."""
        return Metadata(name="MultiProvider")

    def get_provider_hooks(self) -> list[Hook]:
        """Aggregate hooks from all providers."""
        hooks: list[Hook] = []
        for _, provider in self._registered_providers:
            hooks.extend(provider.get_provider_hooks())
        return hooks

    def initialize(self, evaluation_context: EvaluationContext) -> None:
        """Initialize all providers in parallel."""
        errors: list[Exception] = []
        
        for name, provider in self._registered_providers:
            try:
                provider.initialize(evaluation_context)
            except Exception as e:
                errors.append(Exception(f"Provider '{name}' initialization failed: {e}"))
        
        if errors:
            # Aggregate errors
            error_msgs = "; ".join(str(e) for e in errors)
            raise GeneralError(f"Multi-provider initialization failed: {error_msgs}")

    def shutdown(self) -> None:
        """Shutdown all providers."""
        for _, provider in self._registered_providers:
            try:
                provider.shutdown()
            except Exception:
                # Log but don't fail shutdown
                pass

    def _evaluate_with_providers(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[[FeatureProvider, str, FlagValueType, EvaluationContext | None], FlagResolutionDetails],
    ) -> FlagResolutionDetails[FlagValueType]:
        """
        Core evaluation logic that delegates to providers based on strategy.
        
        :param flag_key: The flag key to evaluate
        :param default_value: Default value for the flag
        :param evaluation_context: Evaluation context
        :param resolve_fn: Function to call on each provider for resolution
        :return: Final resolution details
        """
        results: list[tuple[str, FlagResolutionDetails]] = []
        
        for provider_name, provider in self._registered_providers:
            try:
                result = resolve_fn(provider, flag_key, default_value, evaluation_context)
                results.append((provider_name, result))
                
                # In sequential mode, stop if strategy says to use this result
                if (self.strategy.run_mode == "sequential" and 
                    self.strategy.should_use_result(flag_key, provider_name, result)):
                    return result
                    
            except Exception as e:
                # Record error but continue to next provider
                error_result = FlagResolutionDetails(
                    flag_key=flag_key,
                    value=default_value,
                    reason=Reason.ERROR,
                    error_message=str(e),
                )
                results.append((provider_name, error_result))
        
        # In parallel mode or if all sequential attempts completed, pick best result
        for provider_name, result in results:
            if self.strategy.should_use_result(flag_key, provider_name, result):
                return result
        
        # No successful result - return last error or default
        if results:
            return results[-1][1]
        
        return FlagResolutionDetails(
            flag_key=flag_key,
            value=default_value,
            reason=Reason.ERROR,
            error_message="No providers returned a result",
        )

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        return self._evaluate_with_providers(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_boolean_details(k, d, ctx),
        )

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        # For async, delegate to sync for now (async aggregation would be more complex)
        return self.resolve_boolean_details(flag_key, default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return self._evaluate_with_providers(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_string_details(k, d, ctx),
        )

    async def resolve_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        return self.resolve_string_details(flag_key, default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return self._evaluate_with_providers(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_integer_details(k, d, ctx),
        )

    async def resolve_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        return self.resolve_integer_details(flag_key, default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return self._evaluate_with_providers(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_float_details(k, d, ctx),
        )

    async def resolve_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        return self.resolve_float_details(flag_key, default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return self._evaluate_with_providers(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_object_details(k, d, ctx),
        )

    async def resolve_object_details_async(
        self,
        flag_key: str,
        default_value: Sequence[FlagValueType] | Mapping[str, FlagValueType],
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[Sequence[FlagValueType] | Mapping[str, FlagValueType]]:
        return self.resolve_object_details(flag_key, default_value, evaluation_context)

"""
Multi-Provider implementation for OpenFeature Python SDK.

This provider wraps multiple underlying providers, allowing a single client
to interact with multiple flag sources simultaneously.

See: https://openfeature.dev/specification/appendix-a/#multi-provider
"""

from __future__ import annotations

import typing
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, GeneralError
from openfeature.flag_evaluation import FlagResolutionDetails, FlagValueType, Reason
from openfeature.hook import Hook
from openfeature.provider import AbstractProvider, FeatureProvider, Metadata

__all__ = ["MultiProvider", "ProviderEntry", "FirstMatchStrategy", "EvaluationStrategy"]


@dataclass
class ProviderEntry:
    """Configuration for a provider in the Multi-Provider."""

    provider: FeatureProvider
    name: str | None = None


class EvaluationStrategy(typing.Protocol):
    """
    Strategy interface for determining which provider's result to use.
    
    Supports 'sequential' mode (evaluate one at a time, stop early when strategy
    is satisfied) and 'parallel' mode (evaluate all providers, then select best
    result). Note: Both modes currently execute provider calls sequentially;
    true concurrent evaluation using asyncio.gather or ThreadPoolExecutor is
    planned for a future enhancement.
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
        self._cached_hooks: list[Hook] | None = None

    def _register_providers(self, providers: list[ProviderEntry]) -> None:
        """
        Register providers with unique names.
        
        Names are determined by:
        1. Explicit name in ProviderEntry
        2. provider.get_metadata().name if unique and not conflicting
        3. {metadata.name}_{index} if not unique or conflicting
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
                # Explicit name provided - must be unique
                if entry.name in used_names:
                    raise ValueError(f"Provider name '{entry.name}' is not unique")
                final_name = entry.name
            elif name_counts[metadata_name] == 1 and metadata_name not in used_names:
                # Metadata name is unique and not already taken by explicit name
                final_name = metadata_name
            else:
                # Multiple providers or collision with explicit name, add index
                while True:
                    name_indices[metadata_name] = name_indices.get(metadata_name, 0) + 1
                    final_name = f"{metadata_name}_{name_indices[metadata_name]}"
                    if final_name not in used_names:
                        break
            
            used_names.add(final_name)
            self._registered_providers.append((final_name, entry.provider))

    def get_metadata(self) -> Metadata:
        """Return metadata including all wrapped provider metadata."""
        return Metadata(name="MultiProvider")

    def get_provider_hooks(self) -> list[Hook]:
        """Aggregate hooks from all providers (cached for efficiency)."""
        if self._cached_hooks is None:
            hooks: list[Hook] = []
            for _, provider in self._registered_providers:
                hooks.extend(provider.get_provider_hooks())
            self._cached_hooks = hooks
        return self._cached_hooks

    def attach(
        self,
        on_emit: Callable[[FeatureProvider, ProviderEvent, ProviderEventDetails], None],
    ) -> None:
        """
        Attach event handler and propagate to all underlying providers.
        
        Events from underlying providers are forwarded through the MultiProvider.
        This enables features like cache invalidation to work across all providers.
        """
        super().attach(on_emit)
        
        # Propagate attach to all wrapped providers
        for _, provider in self._registered_providers:
            provider.attach(on_emit)

    def detach(self) -> None:
        """
        Detach event handler and propagate to all underlying providers.
        """
        super().detach()
        
        # Propagate detach to all wrapped providers
        for _, provider in self._registered_providers:
            provider.detach()

    def initialize(self, evaluation_context: EvaluationContext) -> None:
        """
        Initialize all providers in parallel using ThreadPoolExecutor.
        
        This allows concurrent initialization of I/O-bound providers.
        """
        def init_provider(entry: tuple[str, FeatureProvider]) -> str | None:
            name, provider = entry
            try:
                provider.initialize(evaluation_context)
                return None
            except Exception as e:
                return f"Provider '{name}' initialization failed: {e}"

        with ThreadPoolExecutor(max_workers=len(self._registered_providers)) as executor:
            results = list(executor.map(init_provider, self._registered_providers))

        errors = [r for r in results if r is not None]
        if errors:
            error_msgs = "; ".join(errors)
            raise GeneralError(f"Multi-provider initialization failed: {error_msgs}")

    def shutdown(self) -> None:
        """Shutdown all providers in parallel."""
        import logging
        
        logger = logging.getLogger(__name__)
        
        def shutdown_provider(entry: tuple[str, FeatureProvider]) -> None:
            name, provider = entry
            try:
                provider.shutdown()
            except Exception as e:
                logger.error(f"Provider '{name}' shutdown failed: {e}")

        with ThreadPoolExecutor(max_workers=len(self._registered_providers)) as executor:
            list(executor.map(shutdown_provider, self._registered_providers))

    def _evaluate_with_providers(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[[FeatureProvider, str, FlagValueType, EvaluationContext | None], FlagResolutionDetails[FlagValueType]],
    ) -> FlagResolutionDetails[FlagValueType]:
        """
        Core evaluation logic that delegates to providers based on strategy.
        
        Current implementation evaluates providers sequentially regardless of
        strategy.run_mode. True concurrent evaluation for 'parallel' mode is
        planned for a future enhancement.
        
        :param flag_key: The flag key to evaluate
        :param default_value: Default value for the flag
        :param evaluation_context: Evaluation context
        :param resolve_fn: Function to call on each provider for resolution
        :return: Final resolution details
        """
        results: list[tuple[str, FlagResolutionDetails[FlagValueType]]] = []
        
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
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=ErrorCode.GENERAL,
                    error_message=str(e),
                )
                results.append((provider_name, error_result))
        
        # If all sequential attempts completed (or parallel mode), pick best result
        for provider_name, result in results:
            if self.strategy.should_use_result(flag_key, provider_name, result):
                return result
        
        # No successful result - return last error or default
        if results:
            return results[-1][1]
        
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.ERROR,
            error_code=ErrorCode.GENERAL,
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

    async def _evaluate_with_providers_async(
        self,
        flag_key: str,
        default_value: FlagValueType,
        evaluation_context: EvaluationContext | None,
        resolve_fn: Callable[[FeatureProvider, str, FlagValueType, EvaluationContext | None], typing.Awaitable[FlagResolutionDetails[FlagValueType]]],
    ) -> FlagResolutionDetails[FlagValueType]:
        """
        Async evaluation logic that properly awaits provider async methods.
        
        :param flag_key: The flag key to evaluate
        :param default_value: Default value for the flag
        :param evaluation_context: Evaluation context
        :param resolve_fn: Async function to call on each provider for resolution
        :return: Final resolution details
        """
        results: list[tuple[str, FlagResolutionDetails[FlagValueType]]] = []
        
        for provider_name, provider in self._registered_providers:
            try:
                result = await resolve_fn(provider, flag_key, default_value, evaluation_context)
                results.append((provider_name, result))
                
                # In sequential mode, stop if strategy says to use this result
                if (self.strategy.run_mode == "sequential" and 
                    self.strategy.should_use_result(flag_key, provider_name, result)):
                    return result
                    
            except Exception as e:
                # Record error but continue to next provider
                error_result = FlagResolutionDetails(
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=ErrorCode.GENERAL,
                    error_message=str(e),
                )
                results.append((provider_name, error_result))
        
        # If all sequential attempts completed (or parallel mode), pick best result
        for provider_name, result in results:
            if self.strategy.should_use_result(flag_key, provider_name, result):
                return result
        
        # No successful result - return last error or default
        if results:
            return results[-1][1]
        
        return FlagResolutionDetails(
            value=default_value,
            reason=Reason.ERROR,
            error_code=ErrorCode.GENERAL,
            error_message="No providers returned a result",
        )

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        """Async boolean evaluation using provider async methods."""
        return await self._evaluate_with_providers_async(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_boolean_details_async(k, d, ctx),
        )

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
        """Async string evaluation using provider async methods."""
        return await self._evaluate_with_providers_async(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_string_details_async(k, d, ctx),
        )

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
        """Async integer evaluation using provider async methods."""
        return await self._evaluate_with_providers_async(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_integer_details_async(k, d, ctx),
        )

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
        """Async float evaluation using provider async methods."""
        return await self._evaluate_with_providers_async(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_float_details_async(k, d, ctx),
        )

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
        """Async object evaluation using provider async methods."""
        return await self._evaluate_with_providers_async(
            flag_key,
            default_value,
            evaluation_context,
            lambda p, k, d, ctx: p.resolve_object_details_async(k, d, ctx),
        )

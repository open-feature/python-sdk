import typing

from openfeature._event_support import run_handlers_for_provider
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import (
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.exception import ErrorCode, GeneralError, OpenFeatureError
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider.no_op_provider import NoOpProvider


class ProviderRegistry:
    _default_provider: FeatureProvider
    _providers: typing.Dict[str, FeatureProvider]
    _provider_status: typing.Dict[FeatureProvider, ProviderStatus]

    def __init__(self) -> None:
        self._default_provider = NoOpProvider()
        self._providers = {}
        self._provider_status = {
            self._default_provider: ProviderStatus.READY,
        }

    def set_provider(self, domain: str, provider: FeatureProvider) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")
        providers = self._providers
        if domain in providers:
            old_provider = providers[domain]
            del providers[domain]
            if old_provider not in providers.values():
                self._shutdown_provider(old_provider)
        if provider not in providers.values():
            self._initialize_provider(provider)
        providers[domain] = provider

    def get_provider(self, domain: typing.Optional[str]) -> FeatureProvider:
        if domain is None:
            return self._default_provider
        return self._providers.get(domain, self._default_provider)

    def set_default_provider(self, provider: FeatureProvider) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")
        if self._default_provider:
            self._shutdown_provider(self._default_provider)
        self._default_provider = provider
        self._initialize_provider(provider)

    def get_default_provider(self) -> FeatureProvider:
        return self._default_provider

    def clear_providers(self) -> None:
        self.shutdown()
        self._providers.clear()
        self._default_provider = NoOpProvider()
        self._provider_status = {
            self._default_provider: ProviderStatus.READY,
        }

    def shutdown(self) -> None:
        for provider in {self._default_provider, *self._providers.values()}:
            self._shutdown_provider(provider)

    def _get_evaluation_context(self) -> EvaluationContext:
        # imported here to avoid circular imports
        from openfeature.api import get_evaluation_context

        return get_evaluation_context()

    def _initialize_provider(self, provider: FeatureProvider) -> None:
        try:
            if hasattr(provider, "initialize"):
                provider.initialize(self._get_evaluation_context())
            self.dispatch_event(
                provider, ProviderEvent.PROVIDER_READY, ProviderEventDetails()
            )
        except Exception as err:
            error_code = (
                err.error_code
                if isinstance(err, OpenFeatureError)
                else ErrorCode.GENERAL
            )
            self.dispatch_event(
                provider,
                ProviderEvent.PROVIDER_ERROR,
                ProviderEventDetails(
                    message=f"Provider initialization failed: {err}",
                    error_code=error_code,
                ),
            )

    def _shutdown_provider(self, provider: FeatureProvider) -> None:
        try:
            if hasattr(provider, "shutdown"):
                provider.shutdown()
            self._provider_status[provider] = ProviderStatus.NOT_READY
        except Exception as err:
            self.dispatch_event(
                provider,
                ProviderEvent.PROVIDER_ERROR,
                ProviderEventDetails(
                    message=f"Provider shutdown failed: {err}",
                    error_code=ErrorCode.PROVIDER_FATAL,
                ),
            )

    def get_provider_status(self, provider: FeatureProvider) -> ProviderStatus:
        return self._provider_status.get(provider, ProviderStatus.NOT_READY)

    def dispatch_event(
        self,
        provider: FeatureProvider,
        event: ProviderEvent,
        details: ProviderEventDetails,
    ) -> None:
        self._update_provider_status(provider, event, details)
        run_handlers_for_provider(provider, event, details)

    def _update_provider_status(
        self,
        provider: FeatureProvider,
        event: ProviderEvent,
        details: ProviderEventDetails,
    ) -> None:
        if event == ProviderEvent.PROVIDER_READY:
            self._provider_status[provider] = ProviderStatus.READY
        elif event == ProviderEvent.PROVIDER_STALE:
            self._provider_status[provider] = ProviderStatus.STALE
        elif event == ProviderEvent.PROVIDER_ERROR:
            status = (
                ProviderStatus.FATAL
                if details.error_code == ErrorCode.PROVIDER_FATAL
                else ProviderStatus.ERROR
            )
            self._provider_status[provider] = status


provider_registry = ProviderRegistry()

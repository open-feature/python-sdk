import typing

from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import GeneralError
from openfeature.provider import FeatureProvider
from openfeature.provider.no_op_provider import NoOpProvider


class ProviderRegistry:
    _default_provider: FeatureProvider
    _providers: typing.Dict[str, FeatureProvider]

    def __init__(self) -> None:
        self._default_provider = NoOpProvider()
        self._providers = {}

    def set_provider(self, domain: str, provider: FeatureProvider) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")
        providers = self._providers
        if domain in providers:
            old_provider = providers[domain]
            del providers[domain]
            if old_provider not in providers.values():
                old_provider.shutdown()
        if provider not in providers.values():
            provider.initialize(self._get_evaluation_context())
        providers[domain] = provider

    def get_provider(self, domain: typing.Optional[str]) -> FeatureProvider:
        if domain is None:
            return self._default_provider
        return self._providers.get(domain, self._default_provider)

    def set_default_provider(self, provider: FeatureProvider) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")
        if self._default_provider:
            self._default_provider.shutdown()
        self._default_provider = provider
        provider.initialize(self._get_evaluation_context())

    def get_default_provider(self) -> FeatureProvider:
        return self._default_provider

    def clear_providers(self) -> None:
        for provider in self._providers.values():
            provider.shutdown()
        self._providers.clear()

    def shutdown(self) -> None:
        for provider in {self._default_provider, *self._providers.values()}:
            provider.shutdown()

    def _get_evaluation_context(self) -> EvaluationContext:
        # imported here to avoid circular imports
        from openfeature.api import get_evaluation_context

        return get_evaluation_context()

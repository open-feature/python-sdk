import typing

from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import GeneralError
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider
from openfeature.provider.metadata import Metadata
from openfeature.provider.no_op_provider import NoOpProvider

_provider: FeatureProvider = NoOpProvider()

_evaluation_context = EvaluationContext()

_hooks: typing.List[Hook] = []

_providers: typing.Dict[str, FeatureProvider] = {}


def get_client(
    domain: typing.Optional[str] = None, version: typing.Optional[str] = None
) -> OpenFeatureClient:
    return OpenFeatureClient(domain=domain, version=version)


def set_provider(
    provider: FeatureProvider, domain: typing.Optional[str] = None
) -> None:
    if provider is None:
        raise GeneralError(error_message="No provider")

    if domain:
        _set_domain_provider(domain, provider)
        return

    global _provider
    if _provider:
        _provider.shutdown()
    _provider = provider
    provider.initialize(_evaluation_context)


def _set_domain_provider(domain: str, provider: FeatureProvider) -> None:
    if domain in _providers:
        old_provider = _providers[domain]
        del _providers[domain]
        if old_provider not in _providers.values():
            old_provider.shutdown()
    if provider not in _providers.values():
        provider.initialize(_evaluation_context)
    _providers[domain] = provider


def _get_provider(domain: typing.Optional[str] = None) -> FeatureProvider:
    global _provider
    if domain is None:
        return _provider
    return _providers.get(domain, _provider)


def clear_providers() -> None:
    for provider in _providers.values():
        provider.shutdown()
    _providers.clear()


def get_provider_metadata(domain: typing.Optional[str] = None) -> Metadata:
    return _get_provider(domain).get_metadata()


def get_evaluation_context() -> EvaluationContext:
    global _evaluation_context
    return _evaluation_context


def set_evaluation_context(evaluation_context: EvaluationContext) -> None:
    global _evaluation_context
    if evaluation_context is None:
        raise GeneralError(error_message="No api level evaluation context")
    _evaluation_context = evaluation_context


def add_hooks(hooks: typing.List[Hook]) -> None:
    global _hooks
    _hooks = _hooks + hooks


def clear_hooks() -> None:
    global _hooks
    _hooks = []


def get_hooks() -> typing.List[Hook]:
    global _hooks
    return _hooks


def shutdown() -> None:
    _provider.shutdown()

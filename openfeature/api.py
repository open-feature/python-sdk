import typing

from openfeature import _event_support
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import (
    EventHandler,
    ProviderEvent,
)
from openfeature.exception import GeneralError
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider
from openfeature.provider.metadata import Metadata
from openfeature.provider.registry import ProviderRegistry

_evaluation_context = EvaluationContext()

_hooks: typing.List[Hook] = []

_provider_registry: ProviderRegistry = ProviderRegistry()


def get_client(
    domain: typing.Optional[str] = None, version: typing.Optional[str] = None
) -> OpenFeatureClient:
    return OpenFeatureClient(domain=domain, version=version)


def set_provider(
    provider: FeatureProvider, domain: typing.Optional[str] = None
) -> None:
    if domain is None:
        _provider_registry.set_default_provider(provider)
    else:
        _provider_registry.set_provider(domain, provider)


def clear_providers() -> None:
    _provider_registry.clear_providers()
    _event_support.clear()


def get_provider_metadata(domain: typing.Optional[str] = None) -> Metadata:
    return _provider_registry.get_provider(domain).get_metadata()


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
    _provider_registry.shutdown()


def add_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _event_support.add_global_handler(event, handler)


def remove_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _event_support.remove_global_handler(event, handler)

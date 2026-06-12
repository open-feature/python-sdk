from openfeature._api import _default_api
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import (
    EventHandler,
    ProviderEvent,
)
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider
from openfeature.provider.metadata import Metadata
from openfeature.transaction_context import TransactionContextPropagator

__all__ = [
    "add_handler",
    "add_hooks",
    "clear_evaluation_context",
    "clear_hooks",
    "clear_providers",
    "clear_transaction_context_propagator",
    "get_client",
    "get_evaluation_context",
    "get_hooks",
    "get_provider_metadata",
    "get_transaction_context",
    "remove_handler",
    "set_evaluation_context",
    "set_provider",
    "set_provider_and_wait",
    "set_transaction_context",
    "set_transaction_context_propagator",
    "shutdown",
]


def get_client(
    domain: str | None = None, version: str | None = None
) -> OpenFeatureClient:
    return _default_api.get_client(domain=domain, version=version)


def set_provider(provider: FeatureProvider, domain: str | None = None) -> None:
    _default_api.set_provider(provider, domain)


def set_provider_and_wait(provider: FeatureProvider, domain: str | None = None) -> None:
    _default_api.set_provider_and_wait(provider, domain)


def clear_providers() -> None:
    _default_api.clear_providers()


def get_provider_metadata(domain: str | None = None) -> Metadata:
    return _default_api.get_provider_metadata(domain)


def shutdown() -> None:
    _default_api.shutdown()


def add_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _default_api.add_handler(event, handler)


def remove_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _default_api.remove_handler(event, handler)


def add_hooks(hooks: list[Hook]) -> None:
    _default_api.add_hooks(hooks)


def clear_hooks() -> None:
    _default_api.clear_hooks()


def get_hooks() -> list[Hook]:
    return _default_api.get_hooks()


def get_evaluation_context() -> EvaluationContext:
    return _default_api.get_evaluation_context()


def set_evaluation_context(evaluation_context: EvaluationContext) -> None:
    _default_api.set_evaluation_context(evaluation_context)


def clear_evaluation_context() -> None:
    _default_api.clear_evaluation_context()


def set_transaction_context_propagator(
    transaction_context_propagator: TransactionContextPropagator,
) -> None:
    _default_api.set_transaction_context_propagator(transaction_context_propagator)


def clear_transaction_context_propagator() -> None:
    _default_api.clear_transaction_context_propagator()


def get_transaction_context() -> EvaluationContext:
    return _default_api.get_transaction_context()


def set_transaction_context(evaluation_context: EvaluationContext) -> None:
    _default_api.set_transaction_context(evaluation_context)

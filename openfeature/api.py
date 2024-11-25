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
from openfeature.provider._registry import provider_registry
from openfeature.provider.metadata import Metadata
from openfeature.transaction_context import TransactionContextPropagator
from openfeature.transaction_context.no_op_transaction_context_propagator import (
    NoOpTransactionContextPropagator,
)

__all__ = [
    "add_handler",
    "add_hooks",
    "clear_hooks",
    "clear_providers",
    "get_client",
    "get_evaluation_context",
    "get_hooks",
    "get_provider_metadata",
    "get_transaction_context",
    "remove_handler",
    "set_evaluation_context",
    "set_provider",
    "set_transaction_context",
    "set_transaction_context_propagator",
    "shutdown",
]

_evaluation_context = EvaluationContext()
_evaluation_transaction_context_propagator: TransactionContextPropagator = (
    NoOpTransactionContextPropagator()
)

_hooks: typing.List[Hook] = []


def get_client(
    domain: typing.Optional[str] = None, version: typing.Optional[str] = None
) -> OpenFeatureClient:
    return OpenFeatureClient(domain=domain, version=version)


def set_provider(
    provider: FeatureProvider, domain: typing.Optional[str] = None
) -> None:
    if domain is None:
        provider_registry.set_default_provider(provider)
    else:
        provider_registry.set_provider(domain, provider)


def clear_providers() -> None:
    provider_registry.clear_providers()
    _event_support.clear()


def get_provider_metadata(domain: typing.Optional[str] = None) -> Metadata:
    return provider_registry.get_provider(domain).get_metadata()


def get_evaluation_context() -> EvaluationContext:
    return _evaluation_context


def set_evaluation_context(evaluation_context: EvaluationContext) -> None:
    global _evaluation_context
    if evaluation_context is None:
        raise GeneralError(error_message="No api level evaluation context")
    _evaluation_context = evaluation_context


def set_transaction_context_propagator(
    transaction_context_propagator: TransactionContextPropagator,
) -> None:
    global _evaluation_transaction_context_propagator
    _evaluation_transaction_context_propagator = transaction_context_propagator


def get_transaction_context() -> EvaluationContext:
    return _evaluation_transaction_context_propagator.get_transaction_context()


def set_transaction_context(evaluation_context: EvaluationContext) -> None:
    global _evaluation_transaction_context_propagator
    _evaluation_transaction_context_propagator.set_transaction_context(
        evaluation_context
    )


def add_hooks(hooks: typing.List[Hook]) -> None:
    global _hooks
    _hooks = _hooks + hooks


def clear_hooks() -> None:
    global _hooks
    _hooks = []


def get_hooks() -> typing.List[Hook]:
    return _hooks


def shutdown() -> None:
    provider_registry.shutdown()


def add_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _event_support.add_global_handler(event, handler)


def remove_handler(event: ProviderEvent, handler: EventHandler) -> None:
    _event_support.remove_global_handler(event, handler)

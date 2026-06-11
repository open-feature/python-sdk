from __future__ import annotations

from openfeature._event_support import EventSupport
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import EventHandler, ProviderEvent
from openfeature.exception import GeneralError
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider._registry import ProviderRegistry
from openfeature.provider.metadata import Metadata
from openfeature.transaction_context import TransactionContextPropagator
from openfeature.transaction_context.no_op_transaction_context_propagator import (
    NoOpTransactionContextPropagator,
)


class OpenFeatureAPI:
    """An independent OpenFeature API instance with its own isolated state.

    Each instance maintains its own providers, evaluation context, hooks,
    event handlers, and transaction context propagator; fully separate from
    the global singleton and from other instances.
    """

    def __init__(self) -> None:
        self._hooks: list[Hook] = []
        self._evaluation_context = EvaluationContext()
        self._transaction_context_propagator: TransactionContextPropagator = (
            NoOpTransactionContextPropagator()
        )
        self._event_support = EventSupport()
        self._provider_registry = ProviderRegistry(
            event_support=self._event_support,
            evaluation_context_getter=self.get_evaluation_context,
        )

    # --- Client creation ---

    def get_client(
        self, domain: str | None = None, version: str | None = None
    ) -> OpenFeatureClient:
        return OpenFeatureClient(domain=domain, version=version, api=self)

    # --- Provider management ---

    def set_provider(
        self, provider: FeatureProvider, domain: str | None = None
    ) -> None:
        if domain is None:
            self._provider_registry.set_default_provider(provider)
        else:
            self._provider_registry.set_provider(domain, provider)

    def set_provider_and_wait(
        self, provider: FeatureProvider, domain: str | None = None
    ) -> None:
        if domain is None:
            self._provider_registry.set_default_provider(provider, wait_for_init=True)
        else:
            self._provider_registry.set_provider(domain, provider, wait_for_init=True)

    def get_provider_metadata(self, domain: str | None = None) -> Metadata:
        return self._provider_registry.get_provider(domain).get_metadata()

    def get_provider(self, domain: str | None = None) -> FeatureProvider:
        return self._provider_registry.get_provider(domain)

    def get_provider_status(self, provider: FeatureProvider) -> ProviderStatus:
        return self._provider_registry.get_provider_status(provider)

    def clear_providers(self) -> None:
        self._provider_registry.clear_providers()
        self._event_support.clear()

    def shutdown(self) -> None:
        # shutdown -> remove providers -> set default provider to NoOp -> remove event handlers
        self.clear_providers()
        # remove hooks
        self.clear_hooks()
        # set evaluation context to default
        self._evaluation_context = EvaluationContext()
        # set propagator to NoOp
        self._transaction_context_propagator = NoOpTransactionContextPropagator()

    # --- Hooks ---

    def add_hooks(self, hooks: list[Hook]) -> None:
        self._hooks = self._hooks + hooks

    def clear_hooks(self) -> None:
        self._hooks = []

    def get_hooks(self) -> list[Hook]:
        return self._hooks

    # --- Evaluation context ---

    def get_evaluation_context(self) -> EvaluationContext:
        return self._evaluation_context

    def set_evaluation_context(self, evaluation_context: EvaluationContext) -> None:
        if evaluation_context is None:
            raise GeneralError(error_message="No api level evaluation context")
        self._evaluation_context = evaluation_context

    def clear_evaluation_context(self) -> None:
        self.set_evaluation_context(EvaluationContext())

    # --- Transaction context ---

    def set_transaction_context_propagator(
        self, transaction_context_propagator: TransactionContextPropagator
    ) -> None:
        self._transaction_context_propagator = transaction_context_propagator

    def clear_transaction_context_propagator(self) -> None:
        self.set_transaction_context_propagator(NoOpTransactionContextPropagator())

    def get_transaction_context(self) -> EvaluationContext:
        return self._transaction_context_propagator.get_transaction_context()

    def set_transaction_context(self, evaluation_context: EvaluationContext) -> None:
        self._transaction_context_propagator.set_transaction_context(evaluation_context)

    # --- Event handlers ---

    def add_handler(self, event: ProviderEvent, handler: EventHandler) -> None:
        self._event_support.add_global_handler(event, handler, self.get_client)

    def remove_handler(self, event: ProviderEvent, handler: EventHandler) -> None:
        self._event_support.remove_global_handler(event, handler)


_default_api = OpenFeatureAPI()

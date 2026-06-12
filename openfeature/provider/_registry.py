from __future__ import annotations

import threading
import typing
import weakref
from collections.abc import Callable

from openfeature.evaluation_context import EvaluationContext
from openfeature.event import (
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.exception import ErrorCode, GeneralError, OpenFeatureError
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider.no_op_provider import NoOpProvider

if typing.TYPE_CHECKING:
    from openfeature._event_support import EventSupport

# spec 1.8.4: provider must not bind to more than one API; we track owning registry per provider, rebinding raises. WeakKeyDictionary lets providers be GC'd
_binding_lock = threading.Lock()
_provider_bindings: weakref.WeakKeyDictionary[FeatureProvider, ProviderRegistry] = (
    weakref.WeakKeyDictionary()
)


def _register_binding(provider: FeatureProvider, owner: ProviderRegistry) -> None:
    try:
        weakref.ref(provider)
    except TypeError as exc:
        raise TypeError(
            f"Provider {type(provider).__name__!r} cannot be tracked because "
            "it is not weak-referenceable. If your provider class uses "
            "__slots__, add '__weakref__' to the slots list."
        ) from exc
    with _binding_lock:
        existing = _provider_bindings.get(provider)
        if existing is not None and existing is not owner:
            raise RuntimeError(
                "Provider is already bound to another OpenFeature API instance."
            )
        _provider_bindings[provider] = owner


def _unregister_binding(provider: FeatureProvider, owner: ProviderRegistry) -> None:
    with _binding_lock:
        if _provider_bindings.get(provider) is owner:
            del _provider_bindings[provider]


class ProviderRegistry:
    _default_provider: FeatureProvider
    _providers: dict[str, FeatureProvider]
    _provider_status: dict[FeatureProvider, ProviderStatus]
    _lock: threading.RLock

    def __init__(
        self,
        event_support: EventSupport,
        evaluation_context_getter: Callable[[], EvaluationContext],
    ) -> None:
        self._lock = threading.RLock()
        self._default_provider = NoOpProvider()
        self._providers = {}
        self._provider_status = {
            self._default_provider: ProviderStatus.READY,
        }
        self._event_support = event_support
        self._evaluation_context_getter = evaluation_context_getter

    def set_provider(
        self, domain: str, provider: FeatureProvider, wait_for_init: bool = False
    ) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")
        if domain is None:
            raise GeneralError(error_message="No domain")

        _register_binding(provider, self)

        old_provider: FeatureProvider | None = None
        needs_init = False
        with self._lock:
            old_provider = self._providers.get(domain)
            self._providers[domain] = provider
            already_bound = provider is self._default_provider or any(
                p is provider for d, p in self._providers.items() if d != domain
            )
            if not already_bound:
                needs_init = True
                self._provider_status[provider] = ProviderStatus.NOT_READY

        if needs_init:
            self._initialize_provider(provider, wait_for_init=wait_for_init)

        # old-provider shutdown is always async so a hanging shutdown() cannot
        # block set_provider.
        if old_provider is not None and old_provider is not provider:
            self._shutdown_if_unused(old_provider)

    def get_provider(self, domain: str | None) -> FeatureProvider:
        if domain is None:
            return self._default_provider
        return self._providers.get(domain, self._default_provider)

    def set_default_provider(
        self, provider: FeatureProvider, wait_for_init: bool = False
    ) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")

        _register_binding(provider, self)

        old_provider: FeatureProvider | None = None
        needs_init = False
        with self._lock:
            old_provider = self._default_provider
            self._default_provider = provider
            if (
                provider is not old_provider
                and provider not in self._providers.values()
            ):
                needs_init = True
                self._provider_status[provider] = ProviderStatus.NOT_READY

        if needs_init:
            self._initialize_provider(provider, wait_for_init=wait_for_init)

        if old_provider is not None and old_provider is not provider:
            self._shutdown_if_unused(old_provider)

    def get_default_provider(self) -> FeatureProvider:
        return self._default_provider

    def clear_providers(self) -> None:
        self.shutdown()
        with self._lock:
            self._providers.clear()
            self._default_provider = NoOpProvider()
            self._provider_status = {
                self._default_provider: ProviderStatus.READY,
            }

    def shutdown(self) -> None:
        with self._lock:
            providers = {self._default_provider, *self._providers.values()}

        for provider in providers:
            self._shutdown_provider(provider)

    def _get_evaluation_context(self) -> EvaluationContext:
        return self._evaluation_context_getter()

    def _initialize_provider(
        self, provider: FeatureProvider, wait_for_init: bool
    ) -> None:
        provider.attach(self.dispatch_event)
        if not hasattr(provider, "initialize"):
            # nothing async to do; dispatch READY synchronously.
            self.dispatch_event(
                provider, ProviderEvent.PROVIDER_READY, ProviderEventDetails()
            )
            return
        if wait_for_init:
            self._run_initialize(provider, raise_on_error=True)
            return

        thread = threading.Thread(
            target=self._run_initialize,
            args=(provider,),
            kwargs={"raise_on_error": False},
            daemon=True,
        )
        thread.start()

    def _run_initialize(
        self, provider: FeatureProvider, raise_on_error: bool = False
    ) -> None:
        try:
            provider.initialize(self._get_evaluation_context())
            # stale init: provider was replaced/shut down during initialize(); drop event.
            # Check active registration, not _provider_status, since replaced providers
            # remain in _provider_status until async shutdown pops them.
            with self._lock:
                if (
                    provider is not self._default_provider
                    and provider not in self._providers.values()
                ):
                    return
            self.dispatch_event(
                provider, ProviderEvent.PROVIDER_READY, ProviderEventDetails()
            )
        except Exception as err:
            # stale init: provider was replaced/shut down during initialize(); drop event.
            # Check active registration, not _provider_status, since replaced providers
            # remain in _provider_status until async shutdown pops them.
            with self._lock:
                if (
                    provider is not self._default_provider
                    and provider not in self._providers.values()
                ):
                    return
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
            if raise_on_error:
                raise

    def _shutdown_if_unused(self, provider: FeatureProvider) -> None:
        # only shut down if no longer referenced. shutdown runs on a daemon
        # thread so a hanging shutdown() cannot block the caller.
        if self._is_active(provider):
            return

        thread = threading.Thread(
            target=self._shutdown_provider,
            args=(provider,),
            kwargs={"abort_if_re_registered": True},
            daemon=True,
        )
        thread.start()

    def _is_active(self, provider: FeatureProvider) -> bool:
        with self._lock:
            return (
                provider is self._default_provider
                or provider in self._providers.values()
            )

    def _shutdown_provider(
        self, provider: FeatureProvider, abort_if_re_registered: bool = False
    ) -> None:
        try:
            # abort if re-registered before shutdown() to avoid tearing down the freshly-registered instance
            if abort_if_re_registered and self._is_active(provider):
                return
            if hasattr(provider, "shutdown"):
                provider.shutdown()
            # abort if re-registered during shutdown(); leave status and event wiring intact
            if abort_if_re_registered and self._is_active(provider):
                return
            with self._lock:
                self._provider_status.pop(provider, None)
        except Exception as err:
            self.dispatch_event(
                provider,
                ProviderEvent.PROVIDER_ERROR,
                ProviderEventDetails(
                    message=f"Provider shutdown failed: {err}",
                    error_code=ErrorCode.PROVIDER_FATAL,
                ),
            )
        provider.detach()
        _unregister_binding(provider, self)

    def get_provider_status(self, provider: FeatureProvider) -> ProviderStatus:
        return self._provider_status.get(provider, ProviderStatus.NOT_READY)

    def dispatch_event(
        self,
        provider: FeatureProvider,
        event: ProviderEvent,
        details: ProviderEventDetails,
    ) -> None:
        self._update_provider_status(provider, event, details)
        self._event_support.run_handlers_for_provider(provider, event, details)

    def _update_provider_status(
        self,
        provider: FeatureProvider,
        event: ProviderEvent,
        details: ProviderEventDetails,
    ) -> None:
        with self._lock:
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

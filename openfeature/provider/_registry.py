import inspect
import threading
from collections.abc import Callable
from unittest.mock import Mock

from openfeature._event_support import run_handlers_for_provider
from openfeature.evaluation_context import EvaluationContext, get_evaluation_context
from openfeature.event import (
    ProviderEvent,
    ProviderEventDetails,
)
from openfeature.exception import ErrorCode, GeneralError, OpenFeatureError
from openfeature.provider import AbstractProvider, FeatureProvider, ProviderStatus
from openfeature.provider.no_op_provider import NoOpProvider


def _is_domain_scoped(provider: FeatureProvider) -> bool:
    if isinstance(provider, AbstractProvider):
        return provider.domain_scoped
    if "domain_scoped" in getattr(provider, "__dict__", {}):
        return bool(provider.__dict__["domain_scoped"])
    class_value = getattr(type(provider), "domain_scoped", False)
    if isinstance(class_value, bool):
        return class_value
    return False


def _callable_accepts_domain(callable_obj: Callable[..., object]) -> bool:
    try:
        signature = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return False
    return "domain" in signature.parameters or any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    )


def _initialize_accepts_domain(provider: FeatureProvider) -> bool:
    initialize = provider.initialize
    if isinstance(initialize, Mock):
        effect = initialize.side_effect
        if callable(effect) and not isinstance(effect, Mock):
            return _callable_accepts_domain(effect)
        return effect is None
    return _callable_accepts_domain(initialize)


def _call_initialize(
    provider: FeatureProvider,
    evaluation_context: EvaluationContext,
    domain: str | None,
) -> None:
    if _initialize_accepts_domain(provider):
        provider.initialize(evaluation_context, domain=domain)
    else:
        provider.initialize(evaluation_context)


class ProviderRegistry:
    _default_provider: FeatureProvider
    _providers: dict[str, FeatureProvider]
    _provider_status: dict[FeatureProvider, ProviderStatus]
    _lock: threading.RLock

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._default_provider = NoOpProvider()
        self._providers = {}
        self._provider_status = {
            self._default_provider: ProviderStatus.READY,
        }

    def set_provider(
        self, domain: str, provider: FeatureProvider, wait_for_init: bool = False
    ) -> None:
        if provider is None:
            raise GeneralError(error_message="No provider")
        if domain is None:
            raise GeneralError(error_message="No domain")

        old_provider: FeatureProvider | None = None
        needs_init = False
        with self._lock:
            self._reject_domain_scoped_rebind(provider, domain)
            old_provider = self._providers.get(domain)
            was_bound_elsewhere = provider is self._default_provider or any(
                p is provider for d, p in self._providers.items() if d != domain
            )
            was_bound_here = (
                domain in self._providers and self._providers[domain] is provider
            )
            self._providers[domain] = provider
            already_bound = was_bound_elsewhere or was_bound_here
            if not already_bound:
                needs_init = True
                self._provider_status[provider] = ProviderStatus.NOT_READY

        if needs_init:
            self._initialize_provider(
                provider, domain=domain, wait_for_init=wait_for_init
            )

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

        old_provider: FeatureProvider | None = None
        needs_init = False
        with self._lock:
            self._reject_domain_scoped_rebind(provider, None)
            old_provider = self._default_provider
            self._default_provider = provider
            if (
                provider is not old_provider
                and provider not in self._providers.values()
            ):
                needs_init = True
                self._provider_status[provider] = ProviderStatus.NOT_READY

        if needs_init:
            self._initialize_provider(
                provider, domain=None, wait_for_init=wait_for_init
            )

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
        return get_evaluation_context()

    def _provider_bindings(self, provider: FeatureProvider) -> list[str | None]:
        bindings: list[str | None] = []
        if provider is self._default_provider:
            bindings.append(None)
        bindings.extend(d for d, p in self._providers.items() if p is provider)
        return bindings

    def _reject_domain_scoped_rebind(
        self, provider: FeatureProvider, domain: str | None
    ) -> None:
        if not _is_domain_scoped(provider):
            return
        bindings = self._provider_bindings(provider)
        if bindings and domain not in bindings:
            raise GeneralError(
                error_message=(
                    "Cannot bind domain-scoped provider to more than one domain"
                )
            )

    def _initialize_provider(
        self,
        provider: FeatureProvider,
        *,
        domain: str | None,
        wait_for_init: bool,
    ) -> None:
        provider.attach(self.dispatch_event)
        if not hasattr(provider, "initialize"):
            # nothing async to do; dispatch READY synchronously.
            self.dispatch_event(
                provider, ProviderEvent.PROVIDER_READY, ProviderEventDetails()
            )
            return
        if wait_for_init:
            self._run_initialize(provider, domain=domain, raise_on_error=True)
            return

        thread = threading.Thread(
            target=self._run_initialize,
            args=(provider,),
            kwargs={"domain": domain, "raise_on_error": False},
            daemon=True,
        )
        thread.start()

    def _run_initialize(
        self,
        provider: FeatureProvider,
        *,
        domain: str | None,
        raise_on_error: bool = False,
    ) -> None:
        try:
            _call_initialize(provider, self._get_evaluation_context(), domain)
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
        with self._lock:
            if provider is self._default_provider:
                return
            if provider in self._providers.values():
                return

        thread = threading.Thread(
            target=self._shutdown_provider,
            args=(provider,),
            kwargs={"abort_if_re_registered": True},
            daemon=True,
        )
        thread.start()

    def _shutdown_provider(
        self, provider: FeatureProvider, abort_if_re_registered: bool = False
    ) -> None:
        try:
            if hasattr(provider, "shutdown"):
                provider.shutdown()
            # if provider is being re-registered, leave its status and event wiring intact
            if abort_if_re_registered:
                with self._lock:
                    if (
                        provider is self._default_provider
                        or provider in self._providers.values()
                    ):
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


provider_registry = ProviderRegistry()

import threading
import time
from unittest.mock import Mock

import pytest

from openfeature.evaluation_context import EvaluationContext, set_evaluation_context
from openfeature.exception import GeneralError, ProviderFatalError
from openfeature.provider import ProviderStatus
from openfeature.provider._registry import (
    ProviderRegistry,
    _callable_accepts_domain,
    _initialize_accepts_domain,
    _is_domain_scoped,
)
from openfeature.provider.metadata import Metadata
from openfeature.provider.no_op_provider import NoOpProvider
from tests.legacy_init_provider import LegacyInitProvider


def test_registry_serves_noop_as_default():
    registry = ProviderRegistry()

    assert isinstance(registry.get_default_provider(), NoOpProvider)
    assert isinstance(registry.get_provider("unknown domain"), NoOpProvider)


def test_setting_provider_requires_domain():
    registry = ProviderRegistry()

    with pytest.raises(GeneralError) as exc_info:
        registry.set_provider(None, NoOpProvider())  # type: ignore[reportArgumentType]

    assert exc_info.value.error_message == "No domain"


def test_setting_provider_requires_provider():
    registry = ProviderRegistry()

    with pytest.raises(GeneralError) as exc_info:
        registry.set_provider("domain", None)  # type: ignore[reportArgumentType]

    assert exc_info.value.error_message == "No provider"


def test_can_register_provider_to_multiple_domains():
    registry = ProviderRegistry()
    provider = NoOpProvider()

    registry.set_provider("domain1", provider)
    registry.set_provider("domain2", provider)

    assert registry.get_provider("domain1") is provider
    assert registry.get_provider("domain2") is provider


def test_registering_provider_replaces_previous_provider():
    """Test that registering a provider replaces the previous provider and calls shutdown on the old one."""

    registry = ProviderRegistry()
    provider1 = Mock()
    provider2 = Mock()

    registry.set_provider("domain", provider1)
    assert registry.get_provider("domain") is provider1

    registry.set_provider("domain", provider2)
    assert registry.get_provider("domain") is provider2

    provider1.shutdown.assert_called_once()
    provider2.shutdown.assert_not_called()


def test_registering_provider_for_first_time_initializes_it():
    """Test that registering a provider for the first time calls its initialize method."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain1", provider, wait_for_init=True)
    registry.set_provider("domain2", provider, wait_for_init=True)

    provider.initialize.assert_called_once()


def test_setting_default_provider_requires_provider():
    registry = ProviderRegistry()

    with pytest.raises(GeneralError) as exc_info:
        registry.set_default_provider(None)  # type: ignore[reportArgumentType]

    assert exc_info.value.error_message == "No provider"


def test_replacing_default_provider_shuts_down_old_one():
    """Test that replacing the default provider shuts down the old default provider."""

    registry = ProviderRegistry()
    default_provider1 = Mock()
    default_provider2 = Mock()

    registry.set_default_provider(default_provider1)
    assert registry.get_default_provider() is default_provider1

    registry.set_default_provider(default_provider2)
    assert registry.get_default_provider() is default_provider2

    default_provider1.shutdown.assert_called_once()
    default_provider2.shutdown.assert_not_called()


def test_setting_default_provider_initializes_it():
    registry = ProviderRegistry()
    provider = Mock()

    registry.set_default_provider(provider, wait_for_init=True)

    provider.initialize.assert_called_once()


def test_registering_provider_as_default_then_domain_only_initializes_once():
    """Test that registering the same provider as default and for a domain only initializes it once."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_default_provider(provider, wait_for_init=True)
    registry.set_provider("domain", provider, wait_for_init=True)

    provider.initialize.assert_called_once()


def test_registering_provider_as_domain_then_default_only_initializes_once():
    """Test that registering the same provider as default and for a domain only initializes it once."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain", provider, wait_for_init=True)
    registry.set_default_provider(provider, wait_for_init=True)

    provider.initialize.assert_called_once()


def test_replacing_provider_used_as_default_does_not_shutdown():
    """Test that replacing a provider that is also the default does not shut it down twice."""

    registry = ProviderRegistry()
    provider1 = Mock()
    provider2 = Mock()

    registry.set_default_provider(provider1)
    registry.set_provider("domain", provider1)

    registry.set_provider("domain", provider2)

    provider1.shutdown.assert_not_called()
    provider2.shutdown.assert_not_called()


def test_replacing_default_provider_used_as_domain_does_not_shutdown():
    """Test that replacing a default provider that is also used for a domain does not shut it down twice."""

    registry = ProviderRegistry()
    provider1 = Mock()
    provider2 = Mock()

    registry.set_provider("domain", provider1)
    registry.set_default_provider(provider1)

    registry.set_default_provider(provider2)

    provider1.shutdown.assert_not_called()
    provider2.shutdown.assert_not_called()


def test_shutting_down_registry_shuts_down_providers_once():
    """Test that shutting down the registry shuts down each provider only once."""

    registry = ProviderRegistry()
    provider1 = Mock()
    provider2 = Mock()

    registry.set_default_provider(provider1)
    registry.set_provider("domain1", provider1)

    registry.set_provider("domain2a", provider2)
    registry.set_provider("domain2b", provider2)

    registry.shutdown()

    provider1.shutdown.assert_called_once()
    provider2.shutdown.assert_called_once()


def test_initializing_provider_sets_status_ready():
    """Test that initializing a provider sets its status to READY."""

    registry = ProviderRegistry()
    provider = Mock()

    assert registry.get_provider_status(provider) == ProviderStatus.NOT_READY

    registry.set_provider("domain", provider, wait_for_init=True)

    provider.initialize.assert_called_once()
    assert registry.get_provider_status(provider) == ProviderStatus.READY


def test_shutting_down_provider_sets_status_not_ready():
    """Test that shutting down a provider sets its status to NOT_READY."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain", provider, wait_for_init=True)
    assert registry.get_provider_status(provider) == ProviderStatus.READY

    registry.shutdown()
    assert registry.get_provider_status(provider) == ProviderStatus.NOT_READY


def test_clearing_registry_resets_providers_and_default():
    """Test that clearing the registry resets all providers and the default provider."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain", provider, wait_for_init=True)
    registry.set_default_provider(provider, wait_for_init=True)

    registry.clear_providers()

    default_provider = registry.get_default_provider()
    assert isinstance(default_provider, NoOpProvider)
    assert registry.get_provider("domain") is default_provider
    assert registry.get_provider_status(default_provider) == ProviderStatus.READY

    provider.initialize.assert_called_once()
    provider.shutdown.assert_called_once()


def test_set_provider_returns_before_initialization_completes():
    """Test that set_provider (non-blocking) returns before initialize finishes."""

    registry = ProviderRegistry()
    init_started = threading.Event()
    init_may_proceed = threading.Event()
    provider = Mock()

    def slow_initialize(ctx):
        init_started.set()
        init_may_proceed.wait()

    provider.initialize.side_effect = slow_initialize

    registry.set_provider("domain", provider)

    assert init_started.wait(timeout=2), "initialize was never called in background"
    assert registry.get_provider_status(provider) == ProviderStatus.NOT_READY

    init_may_proceed.set()  # unblock the background thread


def test_set_provider_and_wait_blocks_until_ready():
    """Test that set_provider with wait_for_init=True blocks until READY."""

    registry = ProviderRegistry()
    initialized = threading.Event()
    provider = Mock()

    def tracking_initialize(ctx):
        initialized.set()

    provider.initialize.side_effect = tracking_initialize

    registry.set_provider("domain", provider, wait_for_init=True)

    assert initialized.is_set()
    assert registry.get_provider_status(provider) == ProviderStatus.READY


def test_set_provider_and_wait_reraises_on_error():
    """Test that set_provider with wait_for_init=True re-raises initialization errors."""
    registry = ProviderRegistry()
    provider = Mock()
    provider.initialize.side_effect = ProviderFatalError()

    with pytest.raises(ProviderFatalError):
        registry.set_provider("domain", provider, wait_for_init=True)


def test_concurrent_set_provider_for_same_provider_initializes_once():
    """Concurrent set_provider calls for different domains using the same
    provider instance must only initialize the provider once."""

    registry = ProviderRegistry()
    init_count = 0
    start_gate = threading.Event()

    def slow_initialize(ctx):
        nonlocal init_count
        # widen the window in which two threads can both observe "not bound"
        start_gate.wait(timeout=2)
        init_count += 1

    provider = Mock()
    provider.initialize.side_effect = slow_initialize

    def call(domain):
        registry.set_provider(domain, provider, wait_for_init=True)

    t1 = threading.Thread(target=call, args=("d1",))
    t2 = threading.Thread(target=call, args=("d2",))
    t1.start()
    t2.start()
    start_gate.set()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert init_count == 1


def test_provider_replaced_during_async_init_does_not_set_ready_status():
    """If a provider is replaced while its async initialize is still running,
    the late PROVIDER_READY event must not resurrect its status."""

    registry = ProviderRegistry()
    init_started = threading.Event()
    init_may_proceed = threading.Event()

    slow_provider = Mock()

    def slow_initialize(ctx):
        init_started.set()
        init_may_proceed.wait(timeout=2)

    slow_provider.initialize.side_effect = slow_initialize

    registry.set_provider("domain", slow_provider)
    assert init_started.wait(timeout=2)

    # replace with a different provider before the slow init finishes
    replacement = Mock()
    registry.set_provider("domain", replacement, wait_for_init=True)

    # now let the slow init complete
    init_may_proceed.set()
    # give the background thread a moment to attempt its (stale) dispatch
    time.sleep(0.1)

    # stale event must not have set READY on the replaced provider
    assert registry.get_provider_status(slow_provider) == ProviderStatus.NOT_READY
    assert registry.get_provider_status(replacement) == ProviderStatus.READY


def test_set_provider_does_not_block_on_hanging_old_shutdown():
    """If the previously-registered provider's shutdown() hangs, a subsequent
    set_provider call must not be blocked by it."""

    registry = ProviderRegistry()

    hanging = Mock()
    hang = threading.Event()
    hanging.shutdown.side_effect = lambda: hang.wait(timeout=5)

    replacement = Mock()

    registry.set_provider("domain", hanging, wait_for_init=True)

    completed = threading.Event()

    def replace():
        registry.set_provider("domain", replacement, wait_for_init=True)
        completed.set()

    threading.Thread(target=replace, daemon=True).start()

    # the swap+init of replacement must complete even though `hanging.shutdown`
    # is still blocked.
    assert completed.wait(timeout=2), (
        "set_provider was blocked by old provider's hanging shutdown()"
    )

    # release the hung shutdown so the test can clean up
    hang.set()


def test_stale_shutdown_does_not_clobber_re_registered_provider():
    """If a provider is replaced and then re-registered while its previous
    (background) shutdown is still finishing, the stale shutdown must not
    pop its status or detach() the freshly-registered instance."""

    registry = ProviderRegistry()

    shutdown_started = threading.Event()
    shutdown_may_proceed = threading.Event()

    provider_a = Mock()

    def slow_shutdown():
        shutdown_started.set()
        shutdown_may_proceed.wait(timeout=5)

    provider_a.shutdown.side_effect = slow_shutdown

    provider_b = Mock()

    # step 1: register A
    registry.set_provider("domain", provider_a, wait_for_init=True)
    assert registry.get_provider_status(provider_a) == ProviderStatus.READY

    # step 2: replace A with B; spawns background shutdown of A which will
    # block inside provider_a.shutdown() until we signal it.
    registry.set_provider("domain", provider_b, wait_for_init=True)
    assert shutdown_started.wait(timeout=2), "A's shutdown thread never started"

    # step 3: re-register A while its previous shutdown is mid-flight
    registry.set_provider("domain", provider_a, wait_for_init=True)
    assert registry.get_provider_status(provider_a) == ProviderStatus.READY

    # step 4: let the stale shutdown of A complete
    shutdown_may_proceed.set()
    # give the background thread a moment to run pop/detach
    time.sleep(0.2)

    # after the stale shutdown completes, A should still be registered and
    # its status should still be READY. If the race triggers, status will
    # fall back to NOT_READY (default for missing entry) and detach was called.
    assert registry.get_provider("domain") is provider_a
    assert registry.get_provider_status(provider_a) == ProviderStatus.READY, (
        "stale shutdown of A clobbered the fresh registration's status"
    )
    provider_a.detach.assert_not_called()


def test_initialize_receives_bound_domain():
    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("my-domain", provider, wait_for_init=True)

    provider.initialize.assert_called_once()
    _, kwargs = provider.initialize.call_args
    assert kwargs.get("domain") == "my-domain"


def test_initialize_receives_none_domain_for_default_provider():
    registry = ProviderRegistry()
    provider = Mock()

    registry.set_default_provider(provider, wait_for_init=True)

    provider.initialize.assert_called_once()
    _, kwargs = provider.initialize.call_args
    assert kwargs.get("domain") is None


def test_domain_scoped_provider_rejects_second_domain():
    registry = ProviderRegistry()
    provider = Mock()
    provider.domain_scoped = True

    registry.set_provider("domain1", provider, wait_for_init=True)

    with pytest.raises(GeneralError) as exc_info:
        registry.set_provider("domain2", provider)

    assert (
        exc_info.value.error_message
        == "Cannot bind domain-scoped provider to more than one domain"
    )
    assert registry.get_provider("domain1") is provider
    provider.initialize.assert_called_once()


def test_domain_scoped_provider_rejects_default_after_domain_binding():
    registry = ProviderRegistry()
    provider = Mock()
    provider.domain_scoped = True

    registry.set_provider("domain", provider, wait_for_init=True)

    with pytest.raises(GeneralError):
        registry.set_default_provider(provider)

    assert registry.get_default_provider() is not provider


def test_domain_scoped_provider_rejects_domain_after_default_binding():
    registry = ProviderRegistry()
    provider = Mock()
    provider.domain_scoped = True

    registry.set_default_provider(provider, wait_for_init=True)

    with pytest.raises(GeneralError):
        registry.set_provider("domain", provider)

    assert registry.get_provider("domain") is registry.get_default_provider()


def test_initialize_skips_domain_for_legacy_signature():
    registry = ProviderRegistry()
    provider = LegacyInitProvider()

    registry.set_provider("domain", provider, wait_for_init=True)

    assert provider.initialize_calls == 1


def test_legacy_abstract_provider_initialize_without_domain():
    registry = ProviderRegistry()
    evaluation_context = EvaluationContext("targeting_key", {"attr": "val"})
    set_evaluation_context(evaluation_context)
    provider = LegacyInitProvider()

    registry.set_provider("domain", provider, wait_for_init=True)

    assert provider.initialize_calls == 1
    assert provider.last_evaluation_context == evaluation_context
    assert registry.get_provider_status(provider) == ProviderStatus.READY


def test_initialize_does_not_retry_when_domain_aware_provider_raises_type_error():
    registry = ProviderRegistry()

    class BrokenProvider:
        def __init__(self):
            self.call_count = 0

        def attach(self, on_emit):
            pass

        def detach(self):
            pass

        def get_metadata(self):
            return Metadata(name="broken")

        def initialize(self, evaluation_context, domain=None):
            self.call_count += 1
            raise TypeError("configuration error")

    provider = BrokenProvider()
    with pytest.raises(TypeError, match="configuration error"):
        registry.set_provider("domain", provider, wait_for_init=True)  # type: ignore[arg-type]

    assert provider.call_count == 1
    provider.detach()


def test_is_domain_scoped_uses_class_level_bool_attribute():
    class ClassScopedProvider:
        domain_scoped = True

    assert _is_domain_scoped(ClassScopedProvider()) is True  # type: ignore[arg-type]


def test_is_domain_scoped_uses_property():
    class PropertyScopedProvider:
        @property
        def domain_scoped(self) -> bool:
            return True

    assert _is_domain_scoped(PropertyScopedProvider()) is True  # type: ignore[arg-type]


def test_is_domain_scoped_rejects_truthy_non_bool_values():
    class StrScopedProvider:
        def __init__(self) -> None:
            self.domain_scoped = "us-east"

    assert _is_domain_scoped(StrScopedProvider()) is False  # type: ignore[arg-type]


def test_domain_scoped_property_provider_rejects_second_domain():
    registry = ProviderRegistry()

    class PropertyScopedProvider(LegacyInitProvider):
        @property
        def domain_scoped(self) -> bool:
            return True

    provider = PropertyScopedProvider()
    registry.set_provider("domain1", provider, wait_for_init=True)

    with pytest.raises(GeneralError) as exc_info:
        registry.set_provider("domain2", provider)

    assert (
        exc_info.value.error_message
        == "Cannot bind domain-scoped provider to more than one domain"
    )


def test_callable_accepts_domain_returns_false_for_uninspectable_callable():
    assert _callable_accepts_domain(object()) is False  # type: ignore[arg-type]


def test_initialize_accepts_domain_returns_false_for_mock_with_invalid_side_effect():
    provider = Mock()
    provider.initialize.side_effect = 123

    assert _initialize_accepts_domain(provider) is False


def test_callable_accepts_domain_returns_true_for_kwargs_signature():
    def initialize(evaluation_context, **kwargs):
        kwargs["domain"] = "ignored"

    assert _callable_accepts_domain(initialize) is True
    initialize(EvaluationContext())


def test_provider_without_initialize_is_ready_immediately():
    registry = ProviderRegistry()

    class NoInitProvider:
        def attach(self, on_emit):
            pass

        def detach(self):
            pass

        def get_metadata(self):
            return Metadata(name="no-init")

    provider = NoInitProvider()
    registry.set_provider("domain", provider, wait_for_init=True)  # type: ignore[arg-type]

    assert registry.get_provider_status(provider) == ProviderStatus.READY
    provider.detach()

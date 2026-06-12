"""
Barrier-based concurrency regression tests for ProviderRegistry.

Each test forces the exact thread interleaving that caused the documented race
condition before the registry lock was introduced. The threading.Barrier ensures
both threads reach the entry point of the critical section simultaneously, maximising
the chance of hitting the bad interleaving on every run.

These tests would have produced one of the following symptoms without the lock:
  - AssertionError  (e.g. shutdown called twice)
  - KeyError        (concurrent del on the same dict key)
  - Undetected lost update (initialize called twice, silently)
"""

import threading
from unittest.mock import Mock, call

from openfeature.provider._registry import ProviderRegistry


def _make_provider(name: str = "") -> Mock:
    """Return a Mock that satisfies the FeatureProvider protocol well enough for the registry."""
    p = Mock()
    p.get_metadata.return_value = Mock(name=name)
    return p


# ---------------------------------------------------------------------------
# set_provider races
# ---------------------------------------------------------------------------


def test_concurrent_replacement_of_same_domain_shuts_down_old_provider_exactly_once():
    """
    Race: two threads both call set_provider("domain", new_X) while an old provider
    is registered. Without the lock both threads read old_provider, delete the key,
    and call _shutdown_provider — double-shutdown or KeyError on the second del.

    Forced interleaving:
        Thread A ──► barrier.wait() ──► set_provider("domain", new1) ──►
        Thread B ──► barrier.wait() ──► set_provider("domain", new2) ──►

    Invariant: old_provider.shutdown called exactly once.
    """
    registry = ProviderRegistry()
    old_provider = _make_provider("old")
    registry.set_provider("domain", old_provider)

    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def replace(new_provider: Mock) -> None:
        try:
            barrier.wait()
            registry.set_provider("domain", new_provider)
        except Exception as e:
            errors.append(e)

    new1, new2 = _make_provider("new1"), _make_provider("new2")
    threads = [
        threading.Thread(target=replace, args=(new1,)),
        threading.Thread(target=replace, args=(new2,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Exception(s) raised in threads: {errors}"
    old_provider.shutdown.assert_called_once()


def test_concurrent_replacement_of_same_domain_does_not_leave_orphaned_initialized_provider():
    """
    Race: two threads both call set_provider("domain", new_X) while an old provider
    is registered.

    Invariant: any newly introduced provider that gets initialized is either:
      - the provider currently registered for the domain, or
      - subsequently shut down and no longer READY.
    """
    from openfeature.provider import ProviderStatus

    registry = ProviderRegistry()
    registry.set_provider("domain", _make_provider("old"))

    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def replace(new_provider: Mock) -> None:
        try:
            barrier.wait()
            registry.set_provider("domain", new_provider)
        except Exception as e:
            errors.append(e)

    new1, new2 = _make_provider("new1"), _make_provider("new2")
    threads = [
        threading.Thread(target=replace, args=(new1,)),
        threading.Thread(target=replace, args=(new2,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Exception(s) raised in threads: {errors}"

    registered = registry.get_provider("domain")

    for candidate in (new1, new2):
        was_initialized = candidate.initialize.call_count > 0
        is_registered = candidate is registered
        was_shutdown = candidate.shutdown.call_count > 0
        status = registry.get_provider_status(candidate)

        if was_initialized and not is_registered:
            assert was_shutdown, "Initialized provider became orphaned without shutdown"
            assert status == ProviderStatus.NOT_READY

# without locks in registry.py, this fails like 25 times out of 5000
# with locks all tests pass
def test_concurrent_registration_of_same_provider_to_different_domains_initializes_exactly_once():
    """
    Race: two threads call set_provider with the *same* provider object but different
    domains. Without the lock both threads check `provider not in providers.values()`
    simultaneously (True for both, since neither has inserted yet) and both call
    _initialize_provider — double-initialize.

    Forced interleaving:
        Thread A ──► barrier.wait() ──► set_provider("domain1", provider) ──►
        Thread B ──► barrier.wait() ──► set_provider("domain2", provider) ──►

    Invariant: provider.initialize called exactly once.
    """
    registry = ProviderRegistry()
    provider = _make_provider("shared")
    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def register(domain: str) -> None:
        try:
            barrier.wait()
            registry.set_provider(domain, provider)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=register, args=("domain1",)),
        threading.Thread(target=register, args=("domain2",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Exception(s) raised in threads: {errors}"
    provider.initialize.assert_called_once()


# ---------------------------------------------------------------------------
# set_default_provider race
# ---------------------------------------------------------------------------

# without locks in registry.py, this fails like 20 times out of 5000
# with locks all tests pass
def test_concurrent_set_default_provider_shuts_down_old_default_exactly_once():
    """
    Race: two threads both call set_default_provider concurrently while the same
    old default is active. Without the lock both threads read the same old default,
    pass the `not in providers.values()` check, and both call _shutdown_provider —
    double-shutdown.

    Forced interleaving:
        Thread A ──► barrier.wait() ──► set_default_provider(new1) ──►
        Thread B ──► barrier.wait() ──► set_default_provider(new2) ──►

    Invariant: old_default.shutdown called exactly once.
    """
    registry = ProviderRegistry()
    old_default = _make_provider("old_default")
    registry.set_default_provider(old_default)

    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def replace(new_provider: Mock) -> None:
        try:
            barrier.wait()
            registry.set_default_provider(new_provider)
        except Exception as e:
            errors.append(e)

    new1, new2 = _make_provider("new1"), _make_provider("new2")
    threads = [
        threading.Thread(target=replace, args=(new1,)),
        threading.Thread(target=replace, args=(new2,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Exception(s) raised in threads: {errors}"
    old_default.shutdown.assert_called_once()


# ---------------------------------------------------------------------------
# clear_providers race
# ---------------------------------------------------------------------------


def test_concurrent_get_provider_during_clear_never_returns_shut_down_provider():
    """
    Race: one thread calls clear_providers() while another repeatedly calls
    get_provider(). Without the lock there was a window after shutdown() but
    before _providers.clear() where get_provider returned a provider that had
    already been shut down.

    Forced interleaving:
        Thread A ──► barrier.wait() ──► clear_providers() ──►
        Thread B ──► barrier.wait() ──► get_provider() x N ──►

    Invariant: every provider returned by get_provider is either the pre-clear
    provider (READY) or the post-clear NoOp (READY). It must never be a provider
    whose status is NOT_READY (i.e. shut down but still visible in the registry).
    """
    from openfeature.provider import ProviderStatus
    from openfeature.provider.no_op_provider import NoOpProvider

    registry = ProviderRegistry()
    provider = _make_provider("active")
    registry.set_provider("domain", provider)

    barrier = threading.Barrier(2)
    bad_observations: list[str] = []

    def clear() -> None:
        barrier.wait()
        registry.clear_providers()

    def read() -> None:
        barrier.wait()
        for _ in range(200):
            #p = registry.get_provider("domain")
            status = registry.get_provider_status(registry.get_provider("domain"))
            if status == ProviderStatus.NOT_READY:
                bad_observations.append(
                    f"get_provider returned shut-down provider "
                )

    threads = [
        threading.Thread(target=clear),
        threading.Thread(target=read),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not bad_observations, "\n".join(bad_observations)

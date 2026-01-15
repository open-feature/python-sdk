from unittest.mock import Mock

import pytest

from openfeature.exception import GeneralError
from openfeature.provider import ProviderStatus
from openfeature.provider._registry import ProviderRegistry
from openfeature.provider.no_op_provider import NoOpProvider


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

    registry.set_provider("domain1", provider)
    registry.set_provider("domain2", provider)

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

    registry.set_default_provider(provider)

    provider.initialize.assert_called_once()


def test_registering_provider_as_default_then_domain_only_initializes_once():
    """Test that registering the same provider as default and for a domain only initializes it once."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_default_provider(provider)
    registry.set_provider("domain", provider)

    provider.initialize.assert_called_once()


def test_registering_provider_as_domain_then_default_only_initializes_once():
    """Test that registering the same provider as default and for a domain only initializes it once."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain", provider)
    registry.set_default_provider(provider)

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

    registry.set_provider("domain", provider)

    provider.initialize.assert_called_once()
    assert registry.get_provider_status(provider) == ProviderStatus.READY


def test_shutting_down_provider_sets_status_not_ready():
    """Test that shutting down a provider sets its status to NOT_READY."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain", provider)
    assert registry.get_provider_status(provider) == ProviderStatus.READY

    registry.shutdown()
    assert registry.get_provider_status(provider) == ProviderStatus.NOT_READY


def test_clearing_registry_resets_providers_and_default():
    """Test that clearing the registry resets all providers and the default provider."""

    registry = ProviderRegistry()
    provider = Mock()

    registry.set_provider("domain", provider)
    registry.set_default_provider(provider)

    registry.clear_providers()

    default_provider = registry.get_default_provider()
    assert isinstance(default_provider, NoOpProvider)
    assert registry.get_provider("domain") is default_provider
    assert registry.get_provider_status(default_provider) == ProviderStatus.READY

    provider.initialize.assert_called_once()
    provider.shutdown.assert_called_once()

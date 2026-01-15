from unittest.mock import Mock

import pytest

from openfeature.exception import GeneralError
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

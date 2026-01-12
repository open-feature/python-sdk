from unittest.mock import Mock

from openfeature.exception import GeneralError
from openfeature.provider._registry import ProviderRegistry
from openfeature.provider.no_op_provider import NoOpProvider


def test_registry_serves_noop_as_default():
    registry = ProviderRegistry()

    assert isinstance(registry.get_default_provider(), NoOpProvider)
    assert isinstance(registry.get_provider("unknown domain"), NoOpProvider)


def test_setting_provider_requires_domain():
    registry = ProviderRegistry()

    try:
        registry.set_provider(None, NoOpProvider())  # type: ignore[reportArgumentType]
        raise AssertionError(
            "Expected an exception when setting provider with None domain"
        )
    except GeneralError as e:
        assert e.error_message == "No domain"
    except Exception as e:
        raise AssertionError("Expected GeneralError, got {type(e)}") from e


def test_setting_provider_requires_provider():
    registry = ProviderRegistry()

    try:
        registry.set_provider("domain", None)  # type: ignore[reportArgumentType]
        raise AssertionError("Expected an exception when setting provider to None")
    except GeneralError as e:
        assert e.error_message == "No provider"
    except Exception as e:
        raise AssertionError("Expected GeneralError, got {type(e)}") from e


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

    try:
        registry.set_default_provider(None)  # type: ignore[reportArgumentType]
        raise AssertionError(
            "Expected an exception when setting default provider to None"
        )
    except GeneralError as e:
        assert e.error_message == "No provider"
    except Exception as e:
        raise AssertionError("Expected GeneralError, got {type(e)}") from e


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

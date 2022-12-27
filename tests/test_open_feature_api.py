import pytest

from open_feature.exception.error_code import ErrorCode
from open_feature.exception.exceptions import GeneralError
from open_feature.open_feature_api import get_client, get_provider, set_provider
from open_feature.provider.no_op_provider import NoOpProvider


def test_should_not_raise_exception_with_nop_client():
    # Given
    # No provider has been set
    # When
    client = get_client(name="Default Provider", version="1.0")

    # Then
    assert client.name == "Default Provider"
    assert client.version == "1.0"
    assert isinstance(client.provider, NoOpProvider)


def test_should_return_open_feature_client_when_configured_correctly():
    # Given
    set_provider(NoOpProvider())

    # When
    client = get_client(name="No-op Provider", version="1.0")

    # Then
    assert client.name == "No-op Provider"
    assert client.version == "1.0"
    assert isinstance(client.provider, NoOpProvider)


def test_should_try_set_provider_and_fail_if_none_provided():
    # Given
    # When
    with pytest.raises(GeneralError) as ge:
        set_provider(provider=None)

    # Then
    assert ge.value.error_message == "No provider"
    assert ge.value.error_code == ErrorCode.GENERAL


def test_should_return_a_provider_if_setup_correctly():
    # Given
    set_provider(NoOpProvider())

    # When
    provider = get_provider()

    # Then
    assert provider
    assert isinstance(provider, NoOpProvider)

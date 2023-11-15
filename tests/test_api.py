from unittest.mock import MagicMock

import pytest

from openfeature.api import (
    add_hooks,
    clear_hooks,
    get_client,
    get_evaluation_context,
    get_hooks,
    get_provider,
    get_provider_metadata,
    set_evaluation_context,
    set_provider,
    shutdown,
)
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import ErrorCode, GeneralError
from openfeature.hook import Hook
from openfeature.provider.metadata import Metadata
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.provider.provider import FeatureProvider


def test_should_not_raise_exception_with_noop_client():
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


def test_should_invoke_provider_initialize_function_on_newly_registered_provider():
    # Given
    evaluation_context = EvaluationContext("targeting_key", {"attr1": "val1"})
    provider = MagicMock(spec=FeatureProvider)

    # When
    set_evaluation_context(evaluation_context)
    set_provider(provider)

    # Then
    provider.initialize.assert_called_with(evaluation_context)


def test_should_invoke_provider_shutdown_function_once_provider_is_no_longer_in_use():
    # Given
    provider_1 = MagicMock(spec=FeatureProvider)
    provider_2 = MagicMock(spec=FeatureProvider)

    # When
    set_provider(provider_1)
    set_provider(provider_2)

    # Then
    assert provider_1.shutdown.called


def test_should_return_a_provider_if_setup_correctly():
    # Given
    set_provider(NoOpProvider())

    # When
    provider = get_provider()

    # Then
    assert provider
    assert isinstance(provider, NoOpProvider)


def test_should_retrieve_metadata_for_configured_provider():
    # Given
    set_provider(NoOpProvider())

    # When
    metadata = get_provider_metadata()

    # Then
    assert isinstance(metadata, Metadata)
    assert metadata.name == "No-op Provider"


def test_should_raise_an_exception_if_no_evaluation_context_set():
    # Given
    with pytest.raises(GeneralError) as ge:
        set_evaluation_context(evaluation_context=None)
    # Then
    assert ge.value
    assert ge.value.error_message == "No api level evaluation context"
    assert ge.value.error_code == ErrorCode.GENERAL


def test_should_successfully_set_evaluation_context_for_api():
    # Given
    evaluation_context = EvaluationContext("targeting_key", {"attr1": "val1"})

    # When
    set_evaluation_context(evaluation_context)
    global_evaluation_context = get_evaluation_context()

    # Then
    assert global_evaluation_context
    assert global_evaluation_context.targeting_key == evaluation_context.targeting_key
    assert global_evaluation_context.attributes == evaluation_context.attributes


def test_should_add_hooks_to_api_hooks():
    # Given
    hook_1 = MagicMock(spec=Hook)
    hook_2 = MagicMock(spec=Hook)
    clear_hooks()

    # When
    add_hooks([hook_1])
    add_hooks([hook_2])

    # Then
    assert get_hooks() == [hook_1, hook_2]


def test_should_call_provider_shutdown_on_api_shutdown():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    set_provider(provider)

    # When
    shutdown()

    # Then
    assert provider.shutdown.called

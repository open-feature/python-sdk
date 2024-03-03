from unittest.mock import MagicMock

import pytest

from openfeature.api import (
    add_handler,
    add_hooks,
    clear_hooks,
    clear_providers,
    get_client,
    get_evaluation_context,
    get_hooks,
    get_provider_metadata,
    remove_handler,
    set_evaluation_context,
    set_provider,
    shutdown,
)
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import EventDetails, ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, GeneralError
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider, Metadata
from openfeature.provider.no_op_provider import NoOpProvider


def test_should_not_raise_exception_with_noop_client():
    # Given
    # No provider has been set
    # When
    client = get_client()

    # Then
    assert isinstance(client.provider, NoOpProvider)


def test_should_return_open_feature_client_when_configured_correctly():
    # Given
    set_provider(NoOpProvider())

    # When
    client = get_client()

    # Then
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


def test_should_provide_a_function_to_bind_provider_through_domain():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    test_client = get_client("test")
    default_client = get_client()

    # When
    set_provider(provider, domain="test")

    # Then
    assert default_client.provider != provider
    assert default_client.domain is None

    assert test_client.provider == provider
    assert test_client.domain == "test"


def test_should_not_initialize_provider_already_bound_to_another_domain():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    set_provider(provider, "foo")

    # When
    set_provider(provider, "bar")

    # Then
    provider.initialize.assert_called_once()


def test_should_shutdown_unbound_provider():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    set_provider(provider, "foo")

    # When
    other_provider = MagicMock(spec=FeatureProvider)
    set_provider(other_provider, "foo")

    provider.shutdown.assert_called_once()


def test_should_not_shutdown_provider_bound_to_another_domain():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    set_provider(provider, "foo")
    set_provider(provider, "bar")

    # When
    other_provider = MagicMock(spec=FeatureProvider)
    set_provider(other_provider, "foo")

    provider.shutdown.assert_not_called()


def test_shutdown_should_shutdown_every_registered_provider_once():
    # Given
    provider_1 = MagicMock(spec=FeatureProvider)
    provider_2 = MagicMock(spec=FeatureProvider)
    set_provider(provider_1)
    set_provider(provider_1, "foo")
    set_provider(provider_2, "bar")
    set_provider(provider_2, "baz")

    # When
    shutdown()

    # Then
    provider_1.shutdown.assert_called_once()
    provider_2.shutdown.assert_called_once()


def test_clear_providers_shutdowns_every_provider_and_resets_default_provider():
    # Given
    provider_1 = MagicMock(spec=FeatureProvider)
    provider_2 = MagicMock(spec=FeatureProvider)
    set_provider(provider_1)
    set_provider(provider_2, "foo")
    set_provider(provider_2, "bar")

    # When
    clear_providers()

    # Then
    provider_1.shutdown.assert_called_once()
    provider_2.shutdown.assert_called_once()
    assert isinstance(get_client().provider, NoOpProvider)


def test_provider_events():
    spy = MagicMock()

    add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)
    add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )
    add_handler(ProviderEvent.PROVIDER_ERROR, spy.provider_error)
    add_handler(ProviderEvent.PROVIDER_STALE, spy.provider_stale)

    provider = NoOpProvider()

    provider_details = ProviderEventDetails(message="message")
    details = EventDetails.from_provider_event_details(
        provider.get_metadata().name, provider_details
    )

    provider.emit_provider_configuration_changed(provider_details)
    provider.emit_provider_error(provider_details)
    provider.emit_provider_stale(provider_details)

    # NOTE: provider_ready is called immediately after adding the handler
    spy.provider_ready.assert_called_once()
    spy.provider_configuration_changed.assert_called_once_with(details)
    spy.provider_error.assert_called_once_with(details)
    spy.provider_stale.assert_called_once_with(details)


def test_add_remove_event_handler():
    provider = NoOpProvider()
    set_provider(provider)

    spy = MagicMock()

    add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )
    remove_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )

    provider_details = ProviderEventDetails(message="message")
    provider.emit_provider_configuration_changed(provider_details)

    spy.provider_configuration_changed.assert_not_called()


# Requirement 5.3.3
def test_handlers_attached_to_provider_already_in_associated_state_should_run_immediately():
    # Given
    provider = NoOpProvider()
    set_provider(provider)
    spy = MagicMock()

    # When
    add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)

    # Then
    spy.provider_ready.assert_called_once()


def test_provider_ready_handlers_run_if_provider_initialize_function_terminates_normally():
    # Given
    provider = NoOpProvider()
    set_provider(provider)

    spy = MagicMock()
    add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)

    # When
    provider.initialize(get_evaluation_context())

    # Then
    spy.provider_ready.assert_called_once()

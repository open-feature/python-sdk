import threading
import time
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
    set_provider_and_wait,
    shutdown,
)
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import EventDetails, ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, GeneralError, ProviderFatalError
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider, Metadata, ProviderStatus
from openfeature.provider._registry import provider_registry
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.transaction_context import (
    ContextVarsTransactionContextPropagator,
    get_transaction_context,
    set_transaction_context_propagator,
)


def wait_for_mock_call(mock: MagicMock, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if mock.call_count:
            return

        time.sleep(0.01)


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
    set_provider_and_wait(provider)

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
    set_provider_and_wait(provider, "foo")

    # When
    set_provider_and_wait(provider, "bar")

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


# Requirement 1.6.1
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


# Requirement 1.6.2
def test_shutdown_should_reset_api_state():
    # Given
    set_provider(MagicMock(spec=FeatureProvider))
    add_hooks([MagicMock(spec=Hook)])
    set_evaluation_context(EvaluationContext("targeting_key", {"attr1": "val1"}))
    set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

    # When
    shutdown()

    # Then
    provider = provider_registry.get_default_provider()
    assert isinstance(provider, NoOpProvider)

    hooks = get_hooks()
    assert not hooks

    evaluation_context = get_evaluation_context()
    assert evaluation_context.targeting_key is None
    assert not evaluation_context.attributes

    transaction_context = (
        get_transaction_context()
    )  # NoOpTransactionContextPropagator returns a default context
    assert transaction_context.targeting_key is None
    assert not transaction_context.attributes


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
    # Given
    spy = MagicMock()
    provider = NoOpProvider()
    set_provider(provider)

    add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)
    add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )
    add_handler(ProviderEvent.PROVIDER_ERROR, spy.provider_error)
    add_handler(ProviderEvent.PROVIDER_STALE, spy.provider_stale)

    provider_details = ProviderEventDetails(message="message")
    details = EventDetails.from_provider_event_details(
        provider.get_metadata().name, provider_details
    )

    # When
    provider.emit_provider_configuration_changed(provider_details)
    provider.emit_provider_error(provider_details)
    provider.emit_provider_stale(provider_details)

    # Then
    # NOTE: provider_ready is called immediately after adding the handler
    wait_for_mock_call(spy.provider_ready)
    wait_for_mock_call(spy.provider_configuration_changed)
    wait_for_mock_call(spy.provider_error)
    wait_for_mock_call(spy.provider_stale)
    spy.provider_ready.assert_called_once()
    spy.provider_configuration_changed.assert_called_once_with(details)
    spy.provider_error.assert_called_once_with(details)
    spy.provider_stale.assert_called_once_with(details)


def test_add_remove_event_handler():
    # Given
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

    # When
    provider.emit_provider_configuration_changed(provider_details)

    # Then
    spy.provider_configuration_changed.assert_not_called()


# Requirement 5.3.3
def test_handlers_attached_to_provider_already_in_associated_state_should_run_immediately():
    # Given
    provider = NoOpProvider()
    set_provider_and_wait(provider)
    spy = MagicMock()

    # When
    add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)

    # Then
    wait_for_mock_call(spy.provider_ready)
    spy.provider_ready.assert_called_once()


def test_provider_ready_handlers_run_if_provider_initialize_function_terminates_normally():
    # Given
    provider = NoOpProvider()

    spy = MagicMock()
    add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)
    wait_for_mock_call(spy.provider_ready)
    spy.reset_mock()  # reset the mock to avoid counting the immediate call on subscribe

    # When
    set_provider_and_wait(provider)

    # Then
    wait_for_mock_call(spy.provider_ready)
    spy.provider_ready.assert_called_once()


def test_provider_error_handlers_run_if_provider_initialize_function_terminates_abnormally():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    provider.initialize.side_effect = ProviderFatalError()

    spy = MagicMock()
    add_handler(ProviderEvent.PROVIDER_ERROR, spy.provider_error)

    # When
    with pytest.raises(ProviderFatalError):
        set_provider_and_wait(provider)

    # Then
    wait_for_mock_call(spy.provider_error)
    spy.provider_error.assert_called_once()


def test_provider_status_is_updated_after_provider_emits_event():
    # Given
    provider = NoOpProvider()
    set_provider_and_wait(provider)
    client = get_client()

    # When
    provider.emit_provider_error(ProviderEventDetails(error_code=ErrorCode.GENERAL))
    # Then
    assert client.get_provider_status() == ProviderStatus.ERROR

    # When
    provider.emit_provider_error(
        ProviderEventDetails(error_code=ErrorCode.PROVIDER_FATAL)
    )
    # Then
    assert client.get_provider_status() == ProviderStatus.FATAL

    # When
    provider.emit_provider_stale(ProviderEventDetails())
    # Then
    assert client.get_provider_status() == ProviderStatus.STALE

    # When
    provider.emit_provider_ready(ProviderEventDetails())
    # Then
    assert client.get_provider_status() == ProviderStatus.READY


# Non-blocking set_provider tests


def test_set_provider_returns_before_initialization_completes():
    # Given: a provider whose initialize blocks until signalled
    init_started = threading.Event()
    init_may_proceed = threading.Event()

    provider = MagicMock(spec=FeatureProvider)

    def slow_initialize(ctx):
        init_started.set()
        init_may_proceed.wait()

    provider.initialize.side_effect = slow_initialize

    # When
    set_provider(provider)

    # Then: set_provider returned before initialize completed (we reached this line
    # while the background thread is still blocked inside initialize)
    assert init_started.wait(timeout=2), "initialize was never called"
    init_may_proceed.set()  # unblock the background thread


def test_provider_status_is_not_ready_during_async_initialization():
    # Given: a provider whose initialize blocks until signalled
    init_may_proceed = threading.Event()
    provider = MagicMock(spec=FeatureProvider)

    def slow_initialize(ctx):
        init_may_proceed.wait()

    provider.initialize.side_effect = slow_initialize

    # When
    set_provider(provider)
    client = get_client()

    # Then: status is NOT_READY while init is still running
    assert client.get_provider_status() == ProviderStatus.NOT_READY

    # Cleanup: let the background thread finish
    init_may_proceed.set()


def test_set_provider_and_wait_blocks_until_initialization_completes():
    # Given
    initialized = threading.Event()
    provider = MagicMock(spec=FeatureProvider)

    def slow_initialize(ctx):
        initialized.set()

    provider.initialize.side_effect = slow_initialize

    # When
    set_provider_and_wait(provider)

    # Then: initialize was called before set_provider_and_wait returned
    assert initialized.is_set()
    assert get_client().get_provider_status() == ProviderStatus.READY


def test_set_provider_and_wait_reraises_on_failure():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    provider.initialize.side_effect = ProviderFatalError()

    # When / Then
    with pytest.raises(ProviderFatalError):
        set_provider_and_wait(provider)


def test_set_provider_swallows_error_and_emits_provider_error_event():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    error_fired = threading.Event()

    def failing_initialize(ctx):
        raise ProviderFatalError()

    provider.initialize.side_effect = failing_initialize

    spy = MagicMock()

    def on_error(details):
        spy.on_error(details)
        error_fired.set()

    add_handler(ProviderEvent.PROVIDER_ERROR, on_error)

    # When: non-blocking set_provider — must not raise
    set_provider(provider)

    # Then: error event fired, exception was not propagated
    assert error_fired.wait(timeout=2), "PROVIDER_ERROR event was never fired"
    spy.on_error.assert_called_once()

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from openfeature.api import add_hooks, clear_hooks, get_client, set_provider
from openfeature.client import OpenFeatureClient
from openfeature.event import EventDetails, ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, OpenFeatureError
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider
from openfeature.provider.no_op_provider import NoOpProvider


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_value"),
        (str, "String", "get_string_value"),
        (int, 100, "get_integer_value"),
        (float, 10.23, "get_float_value"),
        (
            dict,
            {
                "String": "string",
                "Number": 2,
                "Boolean": True,
            },
            "get_object_value",
        ),
        (
            list,
            ["string1", "string2"],
            "get_object_value",
        ),
    ),
)
def test_should_get_flag_value_based_on_method_type(
    flag_type, default_value, get_method, no_op_provider_client
):
    # Given
    # When
    flag = getattr(no_op_provider_client, get_method)(
        flag_key="Key", default_value=default_value
    )
    # Then
    assert flag is not None
    assert flag == default_value
    assert isinstance(flag, flag_type)


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_details"),
        (str, "String", "get_string_details"),
        (int, 100, "get_integer_details"),
        (float, 10.23, "get_float_details"),
        (
            dict,
            {
                "String": "string",
                "Number": 2,
                "Boolean": True,
            },
            "get_object_details",
        ),
        (
            list,
            ["string1", "string2"],
            "get_object_details",
        ),
    ),
)
def test_should_get_flag_detail_based_on_method_type(
    flag_type, default_value, get_method, no_op_provider_client
):
    # Given
    # When
    flag = getattr(no_op_provider_client, get_method)(
        flag_key="Key", default_value=default_value
    )
    # Then
    assert flag is not None
    assert flag.value == default_value
    assert isinstance(flag.value, flag_type)


def test_should_raise_exception_when_invalid_flag_type_provided(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.evaluate_flag_details(
        flag_type=None, flag_key="Key", default_value=True
    )
    # Then
    assert flag.value
    assert flag.error_message == "Unknown flag type"
    assert flag.error_code == ErrorCode.GENERAL
    assert flag.reason == Reason.ERROR


def test_should_pass_flag_metadata_from_resolution_to_evaluation_details():
    # Given
    provider = InMemoryProvider(
        {
            "Key": InMemoryFlag(
                "true",
                {"true": True, "false": False},
                flag_metadata={"foo": "bar"},
            )
        }
    )
    set_provider(provider, "my-client")

    client = OpenFeatureClient("my-client", None)

    # When
    details = client.get_boolean_details(flag_key="Key", default_value=False)

    # Then
    assert details is not None
    assert details.flag_metadata == {"foo": "bar"}


def test_should_handle_a_generic_exception_thrown_by_a_provider(no_op_provider_client):
    # Given
    exception_hook = MagicMock(spec=Hook)
    exception_hook.after.side_effect = Exception("Generic exception raised")
    no_op_provider_client.add_hooks([exception_hook])
    # When
    flag_details = no_op_provider_client.get_boolean_details(
        flag_key="Key", default_value=True
    )
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert isinstance(flag_details.value, bool)
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_message == "Generic exception raised"


def test_should_handle_an_open_feature_exception_thrown_by_a_provider(
    no_op_provider_client,
):
    # Given
    exception_hook = MagicMock(spec=Hook)
    exception_hook.after.side_effect = OpenFeatureError(
        ErrorCode.GENERAL, "error_message"
    )
    no_op_provider_client.add_hooks([exception_hook])

    # When
    flag_details = no_op_provider_client.get_boolean_details(
        flag_key="Key", default_value=True
    )
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert isinstance(flag_details.value, bool)
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_message == "error_message"


def test_should_return_client_metadata_with_domain():
    # Given
    client = OpenFeatureClient("my-client", None, NoOpProvider())
    # When
    metadata = client.get_metadata()
    # Then
    assert metadata is not None
    assert metadata.domain == "my-client"


def test_should_call_api_level_hooks(no_op_provider_client):
    # Given
    clear_hooks()
    api_hook = MagicMock(spec=Hook)
    add_hooks([api_hook])

    # When
    no_op_provider_client.get_boolean_details(flag_key="Key", default_value=True)

    # Then
    api_hook.before.assert_called_once()
    api_hook.after.assert_called_once()


# Requirement 1.7.5
def test_should_define_a_provider_status_accessor(no_op_provider_client):
    # When
    status = no_op_provider_client.get_provider_status()
    # Then
    assert status is not None
    assert status == ProviderStatus.READY


# Requirement 1.7.6
def test_should_shortcircuit_if_provider_is_not_ready(
    no_op_provider_client, monkeypatch
):
    # Given
    monkeypatch.setattr(
        no_op_provider_client, "get_provider_status", lambda: ProviderStatus.NOT_READY
    )
    spy_hook = MagicMock(spec=Hook)
    no_op_provider_client.add_hooks([spy_hook])
    # When
    flag_details = no_op_provider_client.get_boolean_details(
        flag_key="Key", default_value=True
    )
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_code == ErrorCode.PROVIDER_NOT_READY
    spy_hook.error.assert_called_once()


# Requirement 1.7.7
def test_should_shortcircuit_if_provider_is_in_irrecoverable_error_state(
    no_op_provider_client, monkeypatch
):
    # Given
    monkeypatch.setattr(
        no_op_provider_client, "get_provider_status", lambda: ProviderStatus.FATAL
    )
    spy_hook = MagicMock(spec=Hook)
    no_op_provider_client.add_hooks([spy_hook])
    # When
    flag_details = no_op_provider_client.get_boolean_details(
        flag_key="Key", default_value=True
    )
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_code == ErrorCode.PROVIDER_FATAL
    spy_hook.error.assert_called_once()


def test_should_run_error_hooks_if_provider_returns_resolution_with_error_code():
    # Given
    spy_hook = MagicMock(spec=Hook)
    provider = MagicMock(spec=FeatureProvider)
    provider.get_provider_hooks.return_value = []
    provider.resolve_boolean_details.return_value = FlagResolutionDetails(
        value=True,
        reason=Reason.ERROR,
        error_code=ErrorCode.PROVIDER_FATAL,
        error_message="This is an error message",
    )
    set_provider(provider)
    client = get_client()
    client.add_hooks([spy_hook])
    # When
    flag_details = client.get_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_code == ErrorCode.PROVIDER_FATAL
    spy_hook.error.assert_called_once()


def test_provider_events():
    # Given
    provider = NoOpProvider()
    set_provider(provider)

    other_provider = NoOpProvider()
    set_provider(other_provider, "my-domain")

    provider_details = ProviderEventDetails(message="message")
    details = EventDetails.from_provider_event_details(
        provider.get_metadata().name, provider_details
    )

    def emit_all_events(provider):
        provider.emit_provider_configuration_changed(provider_details)
        provider.emit_provider_error(provider_details)
        provider.emit_provider_stale(provider_details)

    spy = MagicMock()

    client = get_client()
    client.add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)
    client.add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )
    client.add_handler(ProviderEvent.PROVIDER_ERROR, spy.provider_error)
    client.add_handler(ProviderEvent.PROVIDER_STALE, spy.provider_stale)

    # When
    emit_all_events(provider)
    emit_all_events(other_provider)

    # Then
    # NOTE: provider_ready is called immediately after adding the handler
    spy.provider_ready.assert_called_once()
    spy.provider_configuration_changed.assert_called_once_with(details)
    spy.provider_error.assert_called_once_with(details)
    spy.provider_stale.assert_called_once_with(details)


def test_add_remove_event_handler():
    # Given
    provider = NoOpProvider()
    set_provider(provider)

    spy = MagicMock()

    client = get_client()
    client.add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )
    client.remove_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )

    provider_details = ProviderEventDetails(message="message")

    # When
    provider.emit_provider_configuration_changed(provider_details)

    # Then
    spy.provider_configuration_changed.assert_not_called()


# Requirement 5.1.2, Requirement 5.1.3
def test_provider_event_late_binding():
    # Given
    provider = NoOpProvider()
    set_provider(provider, "my-domain")
    other_provider = NoOpProvider()

    spy = MagicMock()

    client = get_client("my-domain")
    client.add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, spy.provider_configuration_changed
    )

    set_provider(other_provider, "my-domain")

    provider_details = ProviderEventDetails(message="message from provider")
    other_provider_details = ProviderEventDetails(message="message from other provider")

    details = EventDetails.from_provider_event_details(
        other_provider.get_metadata().name, other_provider_details
    )

    # When
    provider.emit_provider_configuration_changed(provider_details)
    other_provider.emit_provider_configuration_changed(other_provider_details)

    # Then
    spy.provider_configuration_changed.assert_called_once_with(details)


def test_client_handlers_thread_safety():
    provider = NoOpProvider()
    set_provider(provider)

    def add_handlers_task():
        def handler(*args, **kwargs):
            time.sleep(0.005)

        for _ in range(10):
            time.sleep(0.01)
            client = get_client(str(uuid.uuid4()))
            client.add_handler(ProviderEvent.PROVIDER_CONFIGURATION_CHANGED, handler)

    def emit_events_task():
        for _ in range(10):
            time.sleep(0.01)
            provider.emit_provider_configuration_changed(ProviderEventDetails())

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(add_handlers_task)
        f2 = executor.submit(emit_events_task)
        f1.result()
        f2.result()

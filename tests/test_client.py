import inspect
import time
import types
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from openfeature import api
from openfeature.api import add_hooks, clear_hooks, get_client, set_provider
from openfeature.client import OpenFeatureClient, _typecheck_flag_value
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import EventDetails, ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, OpenFeatureError
from openfeature.flag_evaluation import FlagResolutionDetails, FlagType, Reason
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider, ProviderStatus
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.transaction_context import ContextVarsTransactionContextPropagator


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_value"),
        (bool, True, "get_boolean_value_async"),
        (str, "String", "get_string_value"),
        (str, "String", "get_string_value_async"),
        (int, 100, "get_integer_value"),
        (int, 100, "get_integer_value_async"),
        (float, 10.23, "get_float_value"),
        (float, 10.23, "get_float_value_async"),
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
            dict,
            {
                "String": "string",
                "Number": 2,
                "Boolean": True,
            },
            "get_object_value_async",
        ),
        (
            list,
            ["string1", "string2"],
            "get_object_value",
        ),
        (
            list,
            ["string1", "string2"],
            "get_object_value_async",
        ),
    ),
)
@pytest.mark.asyncio
async def test_should_get_flag_value_based_on_method_type(
    flag_type, default_value, get_method, no_op_provider_client
):
    # Given
    # When
    method = getattr(no_op_provider_client, get_method)
    if inspect.iscoroutinefunction(method):
        flag = await method(flag_key="Key", default_value=default_value)
    else:
        flag = method(flag_key="Key", default_value=default_value)
    # Then
    assert flag is not None
    assert flag == default_value
    assert isinstance(flag, flag_type)


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_details"),
        (bool, True, "get_boolean_details_async"),
        (str, "String", "get_string_details"),
        (str, "String", "get_string_details_async"),
        (int, 100, "get_integer_details"),
        (int, 100, "get_integer_details_async"),
        (float, 10.23, "get_float_details"),
        (float, 10.23, "get_float_details_async"),
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
            dict,
            {
                "String": "string",
                "Number": 2,
                "Boolean": True,
            },
            "get_object_details_async",
        ),
        (
            list,
            ["string1", "string2"],
            "get_object_details",
        ),
        (
            list,
            ["string1", "string2"],
            "get_object_details_async",
        ),
    ),
)
@pytest.mark.asyncio
async def test_should_get_flag_detail_based_on_method_type(
    flag_type, default_value, get_method, no_op_provider_client
):
    # Given
    # When
    method = getattr(no_op_provider_client, get_method)
    if inspect.iscoroutinefunction(method):
        flag = await method(flag_key="Key", default_value=default_value)
    else:
        flag = method(flag_key="Key", default_value=default_value)
    # Then
    assert flag is not None
    assert flag.value == default_value
    assert isinstance(flag.value, flag_type)


@pytest.mark.asyncio
async def test_should_raise_exception_when_invalid_flag_type_provided(
    no_op_provider_client,
):
    # Given
    # When
    flag_sync = no_op_provider_client.evaluate_flag_details(
        flag_type=None, flag_key="Key", default_value=True
    )
    flag_async = await no_op_provider_client.evaluate_flag_details_async(
        flag_type=None, flag_key="Key", default_value=True
    )
    # Then
    for flag in [flag_sync, flag_async]:
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


# Requirement 1.7.1, Requirement 1.7.3
def test_should_define_a_provider_status_accessor(no_op_provider_client):
    # When
    status = no_op_provider_client.get_provider_status()
    # Then
    assert status is not None
    assert status == ProviderStatus.READY


# Requirement 1.7.4
def test_provider_should_return_error_status_if_failed():
    # Given
    provider = NoOpProvider()
    set_provider(provider)
    client = get_client()

    provider.emit_provider_error(ProviderEventDetails(error_code=ErrorCode.GENERAL))

    # When
    status = client.get_provider_status()

    # Then
    assert status == ProviderStatus.ERROR


# Requirement 1.7.6, Requirement 1.7.8
@pytest.mark.asyncio
async def test_should_shortcircuit_if_provider_is_not_ready(
    no_op_provider_client, monkeypatch
):
    # Given
    monkeypatch.setattr(
        no_op_provider_client, "get_provider_status", lambda: ProviderStatus.NOT_READY
    )
    spy_hook = MagicMock(spec=Hook)
    no_op_provider_client.add_hooks([spy_hook])
    # When
    flag_details_sync = no_op_provider_client.get_boolean_details(
        flag_key="Key", default_value=True
    )
    spy_hook.error.assert_called_once()
    spy_hook.reset_mock()
    flag_details_async = await no_op_provider_client.get_boolean_details_async(
        flag_key="Key", default_value=True
    )
    # Then
    for flag_details in [flag_details_sync, flag_details_async]:
        assert flag_details is not None
        assert flag_details.value
        assert flag_details.reason == Reason.ERROR
        assert flag_details.error_code == ErrorCode.PROVIDER_NOT_READY
    spy_hook.error.assert_called_once()
    spy_hook.finally_after.assert_called_once()


# Requirement 1.7.5, Requirement 1.7.7
@pytest.mark.asyncio
async def test_should_shortcircuit_if_provider_is_in_irrecoverable_error_state(
    no_op_provider_client, monkeypatch
):
    # Given
    monkeypatch.setattr(
        no_op_provider_client, "get_provider_status", lambda: ProviderStatus.FATAL
    )
    spy_hook = MagicMock(spec=Hook)
    no_op_provider_client.add_hooks([spy_hook])
    # When
    flag_details_sync = no_op_provider_client.get_boolean_details(
        flag_key="Key", default_value=True
    )
    spy_hook.error.assert_called_once()
    spy_hook.reset_mock()
    flag_details_async = await no_op_provider_client.get_boolean_details_async(
        flag_key="Key", default_value=True
    )
    # Then
    for flag_details in [flag_details_sync, flag_details_async]:
        assert flag_details is not None
        assert flag_details.value
        assert flag_details.reason == Reason.ERROR
        assert flag_details.error_code == ErrorCode.PROVIDER_FATAL
    spy_hook.error.assert_called_once()
    spy_hook.finally_after.assert_called_once()


# Requirement 1.7.9
def test_provider_should_return_not_ready_status_after_shutdown(monkeypatch):
    # Given
    provider = NoOpProvider()
    set_provider(provider)
    client = get_client()

    def _shutdown(self) -> None:
        self._status = ProviderStatus.NOT_READY

    monkeypatch.setattr(provider, "shutdown", types.MethodType(_shutdown, provider))

    # When
    api.shutdown()

    status = client.get_provider_status()

    # Then
    assert status == ProviderStatus.NOT_READY


@pytest.mark.asyncio
async def test_should_run_error_hooks_if_provider_returns_resolution_with_error_code():
    # Given
    spy_hook = MagicMock(spec=Hook)
    provider = MagicMock(spec=FeatureProvider)
    provider.get_provider_hooks.return_value = []
    mock_resolution = FlagResolutionDetails(
        value=True,
        reason=Reason.ERROR,
        error_code=ErrorCode.PROVIDER_FATAL,
        error_message="This is an error message",
    )
    provider.resolve_boolean_details.return_value = mock_resolution
    provider.resolve_boolean_details_async.return_value = mock_resolution
    set_provider(provider)
    client = get_client()
    client.add_hooks([spy_hook])
    # When
    flag_details_sync = client.get_boolean_details(flag_key="Key", default_value=True)
    spy_hook.error.assert_called_once()
    spy_hook.reset_mock()
    flag_details_async = await client.get_boolean_details_async(
        flag_key="Key", default_value=True
    )
    # Then
    for flag_details in [flag_details_sync, flag_details_async]:
        assert flag_details is not None
        assert flag_details.value
        assert flag_details.reason == Reason.ERROR
        assert flag_details.error_code == ErrorCode.PROVIDER_FATAL
    spy_hook.error.assert_called_once()


@pytest.mark.asyncio
async def test_client_type_mismatch_exceptions():
    # Given
    client = get_client()
    # When
    flag_details_sync = client.get_boolean_details(
        flag_key="Key", default_value="type mismatch"
    )
    flag_details_async = await client.get_boolean_details_async(
        flag_key="Key", default_value="type mismatch"
    )
    # Then
    for flag_details in [flag_details_sync, flag_details_async]:
        assert flag_details is not None
        assert flag_details.value
        assert flag_details.reason == Reason.ERROR
        assert flag_details.error_code == ErrorCode.TYPE_MISMATCH


@pytest.mark.asyncio
async def test_typecheck_flag_value_general_error():
    # Given
    flag_value = "A"
    flag_type = None
    # When
    err = _typecheck_flag_value(value=flag_value, flag_type=flag_type)
    # Then
    assert err.error_code == ErrorCode.GENERAL
    assert err.error_message == "Unknown flag type"


@pytest.mark.asyncio
async def test_typecheck_flag_value_type_mismatch_error():
    # Given
    flag_value = "A"
    flag_type = FlagType.BOOLEAN
    # When
    err = _typecheck_flag_value(value=flag_value, flag_type=flag_type)
    # Then
    assert err.error_code == ErrorCode.TYPE_MISMATCH
    assert err.error_message == "Expected type <class 'bool'> but got <class 'str'>"


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


# Requirement 5.1.4, Requirement 5.1.5
def test_provider_event_handler_exception():
    # Given
    provider = NoOpProvider()
    set_provider(provider)

    spy = MagicMock()

    client = get_client()
    client.add_handler(ProviderEvent.PROVIDER_ERROR, spy.provider_error)

    # When
    provider.emit_provider_error(
        ProviderEventDetails(error_code=ErrorCode.GENERAL, message="some_error")
    )

    # Then
    spy.provider_error.assert_called_once_with(
        EventDetails(
            flags_changed=None,
            message="some_error",
            error_code=ErrorCode.GENERAL,
            metadata={},
            provider_name="No-op Provider",
        )
    )


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


def test_client_should_merge_contexts():
    api.clear_hooks()
    api.set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

    provider = NoOpProvider()
    provider.resolve_boolean_details = MagicMock(wraps=provider.resolve_boolean_details)
    api.set_provider(provider)

    # Global evaluation context
    global_context = EvaluationContext(
        targeting_key="global", attributes={"global_attr": "global_value"}
    )
    api.set_evaluation_context(global_context)

    # Transaction context
    transaction_context = EvaluationContext(
        targeting_key="transaction",
        attributes={"transaction_attr": "transaction_value"},
    )
    api.set_transaction_context(transaction_context)

    # Client-specific context
    client_context = EvaluationContext(
        targeting_key="client", attributes={"client_attr": "client_value"}
    )
    client = OpenFeatureClient(domain=None, version=None, context=client_context)

    # Invocation-specific context
    invocation_context = EvaluationContext(
        targeting_key="invocation", attributes={"invocation_attr": "invocation_value"}
    )
    flag_input = "flag"
    flag_default = False
    client.get_boolean_details(flag_input, flag_default, invocation_context)

    # Retrieve the call arguments
    args, kwargs = provider.resolve_boolean_details.call_args
    flag_key, default_value, context = (
        kwargs["flag_key"],
        kwargs["default_value"],
        kwargs["evaluation_context"],
    )

    assert flag_key == flag_input
    assert default_value is flag_default
    assert context.targeting_key == "invocation"  # Last one in the merge chain
    assert context.attributes["global_attr"] == "global_value"
    assert context.attributes["transaction_attr"] == "transaction_value"
    assert context.attributes["client_attr"] == "client_value"
    assert context.attributes["invocation_attr"] == "invocation_value"

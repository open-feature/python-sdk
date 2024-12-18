import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from openfeature.api import add_hooks, get_async_client, set_provider
from openfeature.client import AsyncOpenFeatureClient
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, OpenFeatureError
from openfeature.flag_evaluation import Reason
from openfeature.hook import Hook
from openfeature.provider import ProviderStatus
from openfeature.provider.in_memory_provider import AsyncInMemoryProvider, InMemoryFlag
from openfeature.provider.no_op_provider import NoOpProvider


@pytest.mark.parametrize(
    "default, variants, get_method, expected_value",
    (
        ("true", {"true": True, "false": False}, "get_boolean", True),
        ("String", {"String": "Variant"}, "get_string", "Variant"),
        ("Number", {"Number": 100}, "get_integer", 100),
        ("Float", {"Float": 10.23}, "get_float", 10.23),
        (
            "Object",
            {"Object": {"some": "object"}},
            "get_object",
            {"some": "object"},
        ),
    ),
)
@pytest.mark.asyncio
async def test_flag_resolution_to_evaluation_details_async(
    default, variants, get_method, expected_value, clear_hooks_fixture
):
    # Given
    api_hook = MagicMock(spec=Hook)
    add_hooks([api_hook])
    provider = AsyncInMemoryProvider(
        {
            "Key": InMemoryFlag(
                default,
                variants,
                flag_metadata={"foo": "bar"},
            )
        }
    )
    set_provider(provider, "my-async-client")
    client = AsyncOpenFeatureClient("my-async-client", None)
    client.add_hooks([api_hook])
    # When
    details = await getattr(client, f"{get_method}_details")(
        flag_key="Key", default_value=None
    )
    value = await getattr(client, f"{get_method}_value")(
        flag_key="Key", default_value=None
    )
    # Then
    assert details is not None
    assert details.flag_metadata == {"foo": "bar"}
    assert details.value == expected_value
    assert details.value == value


@pytest.mark.asyncio
async def test_should_return_client_metadata_with_domain_async(
    no_op_provider_client_async,
):
    # Given
    # When
    metadata = no_op_provider_client_async.get_metadata()
    # Then
    assert metadata is not None
    assert metadata.domain == "my-async-client"


def test_add_remove_event_handler_async():
    # Given
    provider = NoOpProvider()
    set_provider(provider)
    spy = MagicMock()

    client = get_async_client()
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


def test_client_handlers_thread_safety_async():
    provider = NoOpProvider()
    set_provider(provider)

    def add_handlers_task():
        def handler(*args, **kwargs):
            time.sleep(0.005)

        for _ in range(10):
            time.sleep(0.01)
            client = get_async_client(str(uuid.uuid4()))
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


@pytest.mark.parametrize(
    "provider_status, error_code",
    (
        (ProviderStatus.NOT_READY, ErrorCode.PROVIDER_NOT_READY),
        (ProviderStatus.FATAL, ErrorCode.PROVIDER_FATAL),
    ),
)
@pytest.mark.asyncio
async def test_should_shortcircuit_if_provider_is_not_ready(
    no_op_provider_client_async, monkeypatch, provider_status, error_code
):
    # Given
    monkeypatch.setattr(
        no_op_provider_client_async,
        "get_provider_status",
        lambda: provider_status,
    )
    spy_hook = MagicMock(spec=Hook)
    spy_hook.before.return_value = None
    no_op_provider_client_async.add_hooks([spy_hook])
    # When
    flag_details = await no_op_provider_client_async.get_boolean_details(
        flag_key="Key", default_value=True
    )
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_code == error_code
    spy_hook.error.assert_called_once()


@pytest.mark.parametrize(
    "expected_type, get_method, default_value",
    (
        (bool, "get_boolean_details", True),
        (str, "get_string_details", "default"),
        (int, "get_integer_details", 100),
        (float, "get_float_details", 10.23),
        (dict, "get_object_details", {"some": "object"}),
    ),
)
@pytest.mark.asyncio
async def test_handle_an_open_feature_exception_thrown_by_a_provider_async(
    expected_type,
    get_method,
    default_value,
    no_op_provider_client_async,
):
    # Given
    exception_hook = MagicMock(spec=Hook)
    exception_hook.after.side_effect = OpenFeatureError(
        ErrorCode.GENERAL, "error_message"
    )
    no_op_provider_client_async.add_hooks([exception_hook])

    # When
    flag_details = await getattr(no_op_provider_client_async, get_method)(
        flag_key="Key", default_value=default_value
    )
    # Then
    assert flag_details is not None
    assert flag_details.value
    assert isinstance(flag_details.value, expected_type)
    assert flag_details.reason == Reason.ERROR
    assert flag_details.error_message == "error_message"

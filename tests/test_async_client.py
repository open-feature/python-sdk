import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, AsyncMock

import pytest

from openfeature.api import add_hooks, clear_hooks, get_client_async, set_provider
from openfeature.client import AsyncOpenFeatureClient
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.provider import FeatureProvider
from openfeature.provider.in_memory_provider import InMemoryFlag, AsyncInMemoryProvider
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.hook import AsyncHook


async_hook = MagicMock(spec=AsyncHook)
async_hook.before = AsyncMock(return_value=None)
async_hook.after = AsyncMock(return_value=None)



@pytest.mark.asyncio
async def test_should_pass_flag_metadata_from_resolution_to_evaluation_details_async():
    # Given
    clear_hooks()
    add_hooks([async_hook])
    provider = AsyncInMemoryProvider(
        {
            "Key": InMemoryFlag(
                "true",
                {"true": True, "false": False},
                flag_metadata={"foo": "bar"},
            )
        }
    )
    set_provider(provider, "my-async-client")

    client = AsyncOpenFeatureClient("my-async-client", None)

    # When
    details = await client.get_boolean_details(flag_key="Key", default_value=False)
    # Then
    clear_hooks()
    assert details is not None
    assert details.flag_metadata == {"foo": "bar"}


@pytest.mark.asyncio
async def test_should_return_client_metadata_with_domain_async():
    # Given
    client = AsyncOpenFeatureClient("my-async-client", None, NoOpProvider())
    # When
    metadata = client.get_metadata()
    # Then
    assert metadata is not None
    assert metadata.domain == "my-async-client"


def test_add_remove_event_handler_async():
    # Given
    provider = NoOpProvider()
    set_provider(provider)

    spy = MagicMock()

    client = get_client_async()
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
            client = get_client_async(str(uuid.uuid4()))
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

@pytest.mark.asyncio
async def test_evaluate_boolean_flag_details_async():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    provider.resolve_boolean_details.return_value = FlagResolutionDetails(
        value=True,
        reason=Reason.TARGETING_MATCH,
    )
    set_provider(provider)
    client = get_client_async()
    # When
    flag = await client.evaluate_flag_details(
        flag_type=bool, flag_key="Key", default_value=True
    )

    # Then
    assert flag is not None
    assert flag.value == True

@pytest.mark.asyncio
async def test_evaluate_string_flag_details_async():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    provider.resolve_string_details.return_value = FlagResolutionDetails(
        value="String",
        reason=Reason.TARGETING_MATCH,
    )
    set_provider(provider)
    client = get_client_async()
    # When
    flag = await client.evaluate_flag_details(
        flag_type=str, flag_key="Key", default_value="String"
    )

    # Then
    assert flag is not None
    assert flag.value == "String"

@pytest.mark.asyncio
async def test_evaluate_integer_flag_details():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    provider.resolve_integer_details.return_value = FlagResolutionDetails(
        value=100,
        reason=Reason.TARGETING_MATCH,
    )
    set_provider(provider)
    client = get_client_async()
    # When
    flag = await client.evaluate_flag_details(
        flag_type=int, flag_key="Key", default_value=100
    )

    # Then
    assert flag is not None
    assert flag.value == 100

@pytest.mark.asyncio
async def test_evaluate_float_flag_details_async():
    # Given
    provider = MagicMock(spec=FeatureProvider)
    provider.resolve_float_details.return_value = FlagResolutionDetails(
        value=10.23,
        reason=Reason.TARGETING_MATCH,
    )
    set_provider(provider)
    client = get_client_async()
    # When
    flag = await client.evaluate_flag_details(
        flag_type=float, flag_key="Key", default_value=10.23
    )

    # Then
    assert flag is not None
    assert flag.value == 10.23
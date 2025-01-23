from typing import Optional, Union

import pytest

from openfeature.api import get_client, set_provider
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.provider import AbstractProvider, Metadata


class SynchronousProvider(AbstractProvider):
    def get_metadata(self):
        return Metadata(name="SynchronousProvider")

    def get_provider_hooks(self):
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return FlagResolutionDetails(value=True)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return FlagResolutionDetails(value="string")

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return FlagResolutionDetails(value=1)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return FlagResolutionDetails(value=10.0)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[dict, list],
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Union[dict, list]]:
        return FlagResolutionDetails(value={"key": "value"})


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_value_async"),
        (str, "string", "get_string_value_async"),
        (int, 1, "get_integer_value_async"),
        (float, 10.0, "get_float_value_async"),
        (
            dict,
            {"key": "value"},
            "get_object_value_async",
        ),
    ),
)
@pytest.mark.asyncio
async def test_sync_provider_can_be_called_async(flag_type, default_value, get_method):
    # Given
    set_provider(SynchronousProvider(), "SynchronousProvider")
    client = get_client("SynchronousProvider")
    # When
    async_callable = getattr(client, get_method)
    flag = await async_callable(flag_key="Key", default_value=default_value)
    # Then
    assert flag is not None
    assert flag == default_value
    assert isinstance(flag, flag_type)


@pytest.mark.asyncio
async def test_sync_provider_can_be_extended_async():
    # Given
    class ExtendedAsyncProvider(SynchronousProvider):
        async def resolve_boolean_details_async(
            self,
            flag_key: str,
            default_value: bool,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[bool]:
            return FlagResolutionDetails(value=False)

    set_provider(ExtendedAsyncProvider(), "ExtendedAsyncProvider")
    client = get_client("ExtendedAsyncProvider")
    # When
    flag = await client.get_boolean_value_async(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag is False


# We're not allowing providers to only have async methods
def test_sync_methods_enforced_for_async_providers():
    # Given
    class AsyncProvider(AbstractProvider):
        def get_metadata(self):
            return Metadata(name="AsyncProvider")

        async def resolve_boolean_details_async(
            self,
            flag_key: str,
            default_value: bool,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[bool]:
            return FlagResolutionDetails(value=True)

    # When
    with pytest.raises(TypeError) as exception:
        set_provider(AsyncProvider(), "AsyncProvider")

    # Then
    # assert
    exception_message = str(exception.value)
    assert exception_message.startswith("Can't instantiate abstract class AsyncProvider")
    assert exception_message.__contains__("resolve_boolean_details")


@pytest.mark.asyncio
async def test_async_provider_not_implemented_exception_workaround():
    # Given
    class SyncNotImplementedProvider(AbstractProvider):
        def get_metadata(self):
            return Metadata(name="AsyncProvider")

        async def resolve_boolean_details_async(
            self,
            flag_key: str,
            default_value: bool,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[bool]:
            return FlagResolutionDetails(value=True)

        def resolve_boolean_details(
            self,
            flag_key: str,
            default_value: bool,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[bool]:
            raise NotImplementedError("Use the async method")

        def resolve_string_details(
            self,
            flag_key: str,
            default_value: str,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[str]:
            raise NotImplementedError("Use the async method")

        def resolve_integer_details(
            self,
            flag_key: str,
            default_value: int,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[int]:
            raise NotImplementedError("Use the async method")

        def resolve_float_details(
            self,
            flag_key: str,
            default_value: float,
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[float]:
            raise NotImplementedError("Use the async method")

        def resolve_object_details(
            self,
            flag_key: str,
            default_value: Union[dict, list],
            evaluation_context: Optional[EvaluationContext] = None,
        ) -> FlagResolutionDetails[Union[dict, list]]:
            raise NotImplementedError("Use the async method")

    # When
    set_provider(SyncNotImplementedProvider(), "SyncNotImplementedProvider")
    client = get_client("SyncNotImplementedProvider")
    flag = await client.get_boolean_value_async(flag_key="Key", default_value=False)
    # Then
    assert flag is not None
    assert flag is True

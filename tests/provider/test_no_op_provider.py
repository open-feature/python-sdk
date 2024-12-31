import typing
from numbers import Number

import pytest

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.provider import AsyncAbstractProvider
from openfeature.provider.no_op_provider import NoOpProvider


def test_should_return_no_op_provider_metadata():
    # Given
    # When
    metadata = NoOpProvider().get_metadata()
    # Then
    assert metadata is not None
    assert metadata.name == "No-op Provider"
    assert metadata.is_default_provider


def test_should_resolve_boolean_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_resolve_integer_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_integer_details(flag_key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)


def test_should_resolve_float_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_float_details(flag_key="Key", default_value=10.23)
    # Then
    assert flag is not None
    assert flag.value == 10.23
    assert isinstance(flag.value, Number)


def test_should_resolve_string_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_string_details(flag_key="Key", default_value="String")
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)


def test_should_resolve_list_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_object_details(
        flag_key="Key", default_value=["item1", "item2"]
    )
    # Then
    assert flag is not None
    assert flag.value == ["item1", "item2"]
    assert isinstance(flag.value, list)


def test_should_resolve_object_flag_from_no_op():
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    # When
    flag = NoOpProvider().resolve_object_details(
        flag_key="Key", default_value=return_value
    )
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)


class ConcreteAsyncProvider(AsyncAbstractProvider):
    def get_metadata(self):
        return super().get_metadata()

    async def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return await super().resolve_boolean_details(flag_key, default_value)

    async def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return await super().resolve_string_details(flag_key, default_value)

    async def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return await super().resolve_integer_details(flag_key, default_value)

    async def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return await super().resolve_float_details(flag_key, default_value)

    async def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[dict, list],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[typing.Union[dict, list]]:
        return await super().resolve_object_details(flag_key, default_value)


@pytest.mark.parametrize(
    "get_method, default",
    (
        ("resolve_boolean_details", True),
        ("resolve_string_details", "default"),
        ("resolve_integer_details", 42),
        ("resolve_float_details", 3.14),
        ("resolve_object_details", {"key": "value"}),
    ),
)
@pytest.mark.asyncio
async def test_abstract_provider_throws_not_implemented(get_method, default):
    with pytest.raises(NotImplementedError) as exception:
        provider = ConcreteAsyncProvider()
        await getattr(provider, get_method)("test_flag", default)
    assert str(exception.value) == "Method not implemented"

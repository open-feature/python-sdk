from numbers import Number

from src import open_feature_api as api
from src.provider.no_op_provider import NoOpProvider


def setup():
    api.set_provider(NoOpProvider())
    provider = api.get_provider()
    assert isinstance(provider, NoOpProvider)


def test_should_get_boolean_flag_from_no_op():
    # Given
    api.set_provider(NoOpProvider())
    client = api.get_client()
    # When
    flag = client.get_boolean_details(key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_get_number_flag_from_no_op():
    # Given
    api.set_provider(NoOpProvider())
    client = api.get_client()
    # When
    flag = client.get_number_details(key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)


def test_should_get_string_flag_from_no_op():
    # Given
    api.set_provider(NoOpProvider())
    client = api.get_client()
    # When
    flag = client.get_string_details(key="Key", default_value="String")
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)


def test_should_get_object_flag_from_no_op():
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    api.set_provider(NoOpProvider())
    client = api.get_client()
    # When
    flag = client.get_string_details(key="Key", default_value=return_value)
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)

from numbers import Number

from open_feature import open_feature_api as api
from open_feature.provider.no_op_provider import NoOpProvider


def setup():
    api.set_provider(NoOpProvider())
    provider = api.get_provider()
    assert isinstance(provider, NoOpProvider)


def test_should_get_boolean_flag(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_get_boolean_flag_value(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_boolean_value(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag
    assert isinstance(flag, bool)


def test_should_get_number_flag(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_number_details(flag_key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)


def test_should_get_number_flag_value(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_number_value(flag_key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag == 100
    assert isinstance(flag, Number)


def test_should_get_string_flag(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_string_details(
        flag_key="Key", default_value="String"
    )
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)


def test_should_get_string_flag_value(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_string_value(
        flag_key="Key", default_value="String"
    )
    # Then
    assert flag is not None
    assert flag == "String"
    assert isinstance(flag, str)


def test_should_get_object_flag(no_op_provider_client):
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    # When
    flag = no_op_provider_client.get_object_details(
        flag_key="Key", default_value=return_value
    )
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)


def test_should_get_object_flag_value(no_op_provider_client):
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    # When
    flag = no_op_provider_client.get_object_value(
        flag_key="Key", default_value=return_value
    )
    # Then
    assert flag is not None
    assert flag == return_value
    assert isinstance(flag, dict)

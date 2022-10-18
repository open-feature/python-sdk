from numbers import Number

from open_feature import open_feature_api as api
from open_feature.provider.no_op_provider import NoOpProvider


def setup():
    api.set_provider(NoOpProvider())
    provider = api.get_provider()
    assert isinstance(provider, NoOpProvider)


def test_should_return_no_op_provider_metadata(no_op_provider_client):
    # Given
    # When
    metadata = NoOpProvider().get_metadata()
    # Then
    assert metadata is not None
    assert metadata.name == "No-op Provider"
    assert metadata.is_test_class


def test_should_get_boolean_flag_from_no_op(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_get_number_flag_from_no_op(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_number_details(flag_key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)


def test_should_get_string_flag_from_no_op(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_string_details(
        flag_key="Key", default_value="String"
    )
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)


def test_should_get_object_flag_from_no_op(no_op_provider_client):
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    # When
    flag = no_op_provider_client.get_string_details(
        flag_key="Key", default_value=return_value
    )
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)

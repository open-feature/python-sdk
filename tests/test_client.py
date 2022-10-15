from numbers import Number

from open_feature import open_feature_api as api
from open_feature.provider.no_op_provider import NoOpProvider


def setup():
    api.set_provider(NoOpProvider())
    provider = api.get_provider()
    assert isinstance(provider, NoOpProvider)


def test_should_get_integer_flag_from_no_op(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_integer_details(key="Key", default_value=1)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, int)


def test_should_get_float_flag_from_no_op(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_float_details(key="Key", default_value=1)
    # Then
    assert flag is not None
    assert flag.value == 1
    assert isinstance(flag.value, float)


def test_should_get_number_flag_from_no_op(no_op_provider_client):
    # Given
    # When
    flag = no_op_provider_client.get_number_details(key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)

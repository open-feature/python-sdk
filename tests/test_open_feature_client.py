from numbers import Number

import pytest

from open_feature import open_feature_api as api
from open_feature.exception.exceptions import GeneralError
from open_feature.flag_evaluation.error_code import ErrorCode
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.flag_evaluation.reason import Reason
from open_feature.open_feature_client import OpenFeatureClient
from open_feature.provider.no_op_provider import NoOpProvider
from tests.conftest import TestExceptionHook, TestOpenFeatureErrorHook


def setup():
    api.set_provider(NoOpProvider())
    provider = api.get_provider()
    assert isinstance(provider, NoOpProvider)


def test_should_use_no_op_provider_if_none_provided():
    # Given
    # When
    flag = OpenFeatureClient("No provider", "1.0")._create_provider_evaluation(
        flag_type=FlagType.BOOLEAN, flag_key="Key", default_value=True
    )
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_raise_exception_when_invalid_flag_type_provided():
    # Given
    # When
    with pytest.raises(GeneralError) as ge:
        OpenFeatureClient("No provider", "1.0")._create_provider_evaluation(
            flag_type=None, flag_key="Key", default_value=True
        )
    # Then
    assert ge.value
    assert ge.value.error_message == "Unknown flag type"
    assert ge.value.error_code == ErrorCode.GENERAL


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


def test_should_handle_a_generic_exception_thrown_by_a_provider(no_op_provider_client):
    # Given
    no_op_provider_client.add_hooks([TestExceptionHook()])
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
    no_op_provider_client.add_hooks([TestOpenFeatureErrorHook()])
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

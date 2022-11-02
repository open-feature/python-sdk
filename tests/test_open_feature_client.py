from numbers import Number
from unittest.mock import MagicMock

import pytest

from open_feature import open_feature_api as api
from open_feature.exception.exceptions import GeneralError, OpenFeatureError
from open_feature.flag_evaluation.error_code import ErrorCode
from open_feature.flag_evaluation.reason import Reason
from open_feature.hooks.hook import Hook
from open_feature.open_feature_client import OpenFeatureClient
from open_feature.provider.no_op_provider import NoOpProvider


def setup():
    api.set_provider(NoOpProvider())
    provider = api.get_provider()
    assert isinstance(provider, NoOpProvider)


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_value"),
        (str, "String", "get_string_value"),
        (Number, 100, "get_number_value"),
        (
            dict,
            {
                "String": "string",
                "Number": 2,
                "Boolean": True,
            },
            "get_object_value",
        ),
    ),
)
def test_should_get_flag_value_based_on_method_type(
    flag_type, default_value, get_method, no_op_provider_client
):
    # Given
    # When
    flag = getattr(no_op_provider_client, get_method)(
        flag_key="Key", default_value=default_value
    )
    # Then
    assert flag is not None
    assert flag == default_value
    assert isinstance(flag, flag_type)


@pytest.mark.parametrize(
    "flag_type, default_value, get_method",
    (
        (bool, True, "get_boolean_details"),
        (str, "String", "get_string_details"),
        (Number, 100, "get_number_details"),
        (
            dict,
            {
                "String": "string",
                "Number": 2,
                "Boolean": True,
            },
            "get_object_details",
        ),
    ),
)
def test_should_get_flag_detail_based_on_method_type(
    flag_type, default_value, get_method, no_op_provider_client
):
    # Given
    # When
    flag = getattr(no_op_provider_client, get_method)(
        flag_key="Key", default_value=default_value
    )
    # Then
    assert flag is not None
    assert flag.value == default_value
    assert isinstance(flag.value, flag_type)


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
        "error_message", ErrorCode.GENERAL
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

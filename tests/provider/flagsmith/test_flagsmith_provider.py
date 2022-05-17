from numbers import Number
from unittest.mock import Mock

from src.open_feature import OpenFeature
from src.provider.flagsmith.flagsmith_provider import FlagsmithProvider


def setup():
    flagsmith_mock = Mock()
    OpenFeature.set_provider(FlagsmithProvider(flagsmith=flagsmith_mock))
    provider = OpenFeature.get_provider()
    assert isinstance(provider, FlagsmithProvider)


def test_should_get_boolean_flag_from_flagsmith():
    # Given
    flagsmith_mock = Mock()
    flagsmith_mock.get_value.return_value = True
    OpenFeature.set_provider(FlagsmithProvider(flagsmith=flagsmith_mock))
    provider = OpenFeature.get_provider()
    # When
    flag = provider.get_boolean_value("Key", False)
    # Then
    flagsmith_mock.get_value.assert_called_once()
    assert flag
    assert isinstance(flag, bool)


def test_should_get_number_flag_from_flagsmith():
    # Given
    flagsmith_mock = Mock()
    flagsmith_mock.get_value.return_value = 100
    OpenFeature.set_provider(FlagsmithProvider(flagsmith=flagsmith_mock))
    provider = OpenFeature.get_provider()
    # When
    flag = provider.get_string_value("Key", -1)
    # Then
    flagsmith_mock.get_value.assert_called_once()
    assert flag is 100
    assert isinstance(flag, Number)


def test_should_get_string_flag_from_flagsmith():
    # Given
    flagsmith_mock = Mock()
    flagsmith_mock.get_value.return_value = "String"
    OpenFeature.set_provider(FlagsmithProvider(flagsmith=flagsmith_mock))
    provider = OpenFeature.get_provider()
    # When
    flag = provider.get_string_value("Key", "Not A String")
    # Then
    flagsmith_mock.get_value.assert_called_once()
    assert flag is "String"
    assert isinstance(flag, str)

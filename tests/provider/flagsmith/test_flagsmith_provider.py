from unittest.mock import Mock

from src.open_feature import OpenFeatureProvider
from src.provider.flagsmith.flagsmith_provider import FlagsmithProvider


def setUp():
    OpenFeatureProvider.set_provider(FlagsmithProvider(flagsmith=Mock()))
    provider = OpenFeatureProvider.get_provider()
    assert isinstance(provider, FlagsmithProvider)


def test_should_get_boolean_flag_from_flagsmith():
    # Given
    provider = OpenFeatureProvider.get_provider()
    # When
    flag = provider.get_boolean_value("Key", False)
    # Then
    assert flag

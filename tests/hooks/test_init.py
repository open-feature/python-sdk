from unittest.mock import MagicMock

from open_feature.hooks.hook import Hook
from open_feature.hooks import add_api_hooks, clear_api_hooks, api_hooks


def test_should_add_hooks_to_api_hooks():
    # Given
    hook_1 = MagicMock(spec=Hook)
    hook_2 = MagicMock(spec=Hook)
    clear_api_hooks()

    # When
    add_api_hooks([hook_1])
    add_api_hooks([hook_2])

    # Then
    assert api_hooks() == [hook_1, hook_2]

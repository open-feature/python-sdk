from unittest import mock

import pytest

from openfeature.evaluation_context import EvaluationContext
from openfeature.hook import AsyncHook


@pytest.fixture()
def mock_hook():
    mock_hook = mock.MagicMock()
    mock_hook.supports_flag_value_type.return_value = True
    mock_hook.before.return_value = EvaluationContext()
    mock_hook.after.return_value = None
    mock_hook.error.return_value = None
    mock_hook.finally_after.return_value = None
    return mock_hook


@pytest.fixture()
def mock_hook_async():
    mock_hook = AsyncHook()
    mock_hook.supports_flag_value_type = mock.MagicMock(return_value=True)
    mock_hook.before = mock.AsyncMock(return_value=None)
    mock_hook.after = mock.AsyncMock(return_value=None)
    mock_hook.error = mock.AsyncMock(return_value=None)
    mock_hook.finally_after = mock.AsyncMock(return_value=None)
    return mock_hook

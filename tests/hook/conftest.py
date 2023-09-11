from unittest import mock

import pytest

from openfeature.evaluation_context import EvaluationContext


@pytest.fixture()
def mock_hook():
    mock_hook = mock.MagicMock()
    mock_hook.supports_flag_value_type.return_value = True
    mock_hook.before.return_value = EvaluationContext()
    mock_hook.after.return_value = None
    mock_hook.error.return_value = None
    mock_hook.finally_after.return_value = None
    return mock_hook

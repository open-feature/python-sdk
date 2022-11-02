import pytest

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.exceptions import GeneralError
from open_feature.flag_evaluation.error_code import ErrorCode
from open_feature.open_feature_evaluation_context import (
    api_evaluation_context,
    set_api_evaluation_context,
)


def test_should_raise_an_exception_if_no_evaluation_context_set():
    # Given
    with pytest.raises(GeneralError) as ge:
        set_api_evaluation_context(evaluation_context=None)
    # Then
    assert ge.value
    assert ge.value.error_message == "No api level evaluation context"
    assert ge.value.error_code == ErrorCode.GENERAL


def test_should_successfully_set_evaluation_context_for_api():
    # Given
    evaluation_context = EvaluationContext("targeting_key", {"attr1": "val1"})

    # When
    set_api_evaluation_context(evaluation_context)
    global_evaluation_context = api_evaluation_context()

    # Then
    assert global_evaluation_context
    assert global_evaluation_context.targeting_key == evaluation_context.targeting_key
    assert global_evaluation_context.attributes == evaluation_context.attributes

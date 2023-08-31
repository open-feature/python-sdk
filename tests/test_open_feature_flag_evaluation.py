from open_feature.exception import ErrorCode
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.reason import Reason


def test_evaulation_details_reason_should_be_a_string():
    # Given
    flag_key = "my-flag"
    flag_value = 100
    variant = "1-hundred"
    reason = Reason.DEFAULT
    error_code = ErrorCode.GENERAL
    error_message = "message"

    # When
    flag_details = FlagEvaluationDetails(
        flag_key,
        flag_value,
        variant,
        reason,
        error_code,
        error_message,
    )

    # Then
    assert flag_key == flag_details.flag_key
    assert flag_value == flag_details.value
    assert variant == flag_details.variant
    assert error_code == flag_details.error_code
    assert error_message == flag_details.error_message
    assert reason == flag_details.reason


def test_evaulation_details_reason_should_be_a_string_when_set():
    # Given
    flag_key = "my-flag"
    flag_value = 100
    variant = "1-hundred"
    reason = Reason.DEFAULT
    error_code = ErrorCode.GENERAL
    error_message = "message"

    # When
    flag_details = FlagEvaluationDetails(
        flag_key,
        flag_value,
        variant,
        reason,
        error_code,
        error_message,
    )
    flag_details.reason = Reason.STATIC

    # Then
    assert Reason.STATIC == flag_details.reason

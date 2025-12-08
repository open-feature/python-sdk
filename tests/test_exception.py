from openfeature.exception import ErrorCode


def test_error_code_str():
    assert str(ErrorCode.GENERAL) == "GENERAL"

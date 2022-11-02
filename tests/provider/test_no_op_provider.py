from numbers import Number

from open_feature.provider.no_op_provider import NoOpProvider


def test_should_return_no_op_provider_metadata():
    # Given
    # When
    metadata = NoOpProvider().get_metadata()
    # Then
    assert metadata is not None
    assert metadata.name == "No-op Provider"
    assert metadata.is_default_provider


def test_should_get_boolean_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().get_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_get_number_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().get_number_details(flag_key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)


def test_should_get_string_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().get_string_details(flag_key="Key", default_value="String")
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)


def test_should_get_object_flag_from_no_op():
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    # When
    flag = NoOpProvider().get_object_details(flag_key="Key", default_value=return_value)
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)

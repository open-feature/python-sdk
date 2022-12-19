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


def test_should_resolve_boolean_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value
    assert isinstance(flag.value, bool)


def test_should_resolve_integer_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_integer_details(flag_key="Key", default_value=100)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)


def test_should_resolve_float_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_float_details(flag_key="Key", default_value=10.23)
    # Then
    assert flag is not None
    assert flag.value == 10.23
    assert isinstance(flag.value, Number)


def test_should_resolve_string_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_string_details(flag_key="Key", default_value="String")
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)


def test_should_resolve_list_flag_from_no_op():
    # Given
    # When
    flag = NoOpProvider().resolve_object_details(flag_key="Key", default_value=["item1", "item2"])
    # Then
    assert flag is not None
    assert flag.value == ["item1", "item2"]
    assert isinstance(flag.value, list)


def test_should_resolve_object_flag_from_no_op():
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    # When
    flag = NoOpProvider().resolve_object_details(
        flag_key="Key", default_value=return_value
    )
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)

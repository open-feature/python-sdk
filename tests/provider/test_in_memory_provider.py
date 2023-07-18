from numbers import Number

from open_feature.exception.error_code import ErrorCode
from open_feature.flag_evaluation.reason import Reason
from open_feature.flag_evaluation.resolution_details import FlagResolutionDetails
from open_feature.provider.in_memory_provider import InMemoryProvider, InMemoryFlag


def test_should_return_in_memory_provider_metadata():
    # Given
    provider = InMemoryProvider({})
    # When
    metadata = provider.get_metadata()
    # Then
    assert metadata is not None
    assert metadata.name == "In-Memory Provider"


def test_should_handle_unknown_flags_correctly():
    # Given
    provider = InMemoryProvider({})
    # When
    flag = provider.resolve_boolean_details(flag_key="Key", default_value=True)
    # Then
    assert flag is not None
    assert flag.value is True
    assert isinstance(flag.value, bool)
    assert flag.reason == Reason.ERROR
    assert flag.error_code == ErrorCode.FLAG_NOT_FOUND
    assert flag.error_message == "Flag 'Key' not found"


def test_calls_context_evaluator_if_present():
    # Given
    def context_evaluator(flag: InMemoryFlag, evaluation_context: dict):
        return FlagResolutionDetails(
            value=False,
            reason=Reason.TARGETING_MATCH,
        )

    provider = InMemoryProvider(
        {
            "Key": InMemoryFlag(
                "Key",
                "true",
                {"true": True, "false": False},
                context_evaluator=context_evaluator,
            )
        }
    )
    # When
    flag = provider.resolve_boolean_details(flag_key="Key", default_value=False)
    # Then
    assert flag is not None
    assert flag.value is False
    assert isinstance(flag.value, bool)
    assert flag.reason == Reason.TARGETING_MATCH


def test_should_resolve_boolean_flag_from_in_memory():
    # Given
    provider = InMemoryProvider(
        {"Key": InMemoryFlag("Key", "true", {"true": True, "false": False})}
    )
    # When
    flag = provider.resolve_boolean_details(flag_key="Key", default_value=False)
    # Then
    assert flag is not None
    assert flag.value is True
    assert isinstance(flag.value, bool)
    assert flag.variant == "true"


def test_should_resolve_integer_flag_from_in_memory():
    # Given
    provider = InMemoryProvider(
        {"Key": InMemoryFlag("Key", "hundred", {"zero": 0, "hundred": 100})}
    )
    # When
    flag = provider.resolve_integer_details(flag_key="Key", default_value=0)
    # Then
    assert flag is not None
    assert flag.value == 100
    assert isinstance(flag.value, Number)
    assert flag.variant == "hundred"


def test_should_resolve_float_flag_from_in_memory():
    # Given
    provider = InMemoryProvider(
        {"Key": InMemoryFlag("Key", "ten", {"zero": 0.0, "ten": 10.23})}
    )
    # When
    flag = provider.resolve_float_details(flag_key="Key", default_value=0.0)
    # Then
    assert flag is not None
    assert flag.value == 10.23
    assert isinstance(flag.value, Number)
    assert flag.variant == "ten"


def test_should_resolve_string_flag_from_in_memory():
    # Given
    provider = InMemoryProvider(
        {
            "Key": InMemoryFlag(
                "Key",
                "stringVariant",
                {"defaultVariant": "Default", "stringVariant": "String"},
            )
        }
    )
    # When
    flag = provider.resolve_string_details(flag_key="Key", default_value="Default")
    # Then
    assert flag is not None
    assert flag.value == "String"
    assert isinstance(flag.value, str)
    assert flag.variant == "stringVariant"


def test_should_resolve_list_flag_from_in_memory():
    # Given
    provider = InMemoryProvider(
        {
            "Key": InMemoryFlag(
                "Key", "twoItems", {"empty": [], "twoItems": ["item1", "item2"]}
            )
        }
    )
    # When
    flag = provider.resolve_object_details(flag_key="Key", default_value=[])
    # Then
    assert flag is not None
    assert flag.value == ["item1", "item2"]
    assert isinstance(flag.value, list)
    assert flag.variant == "twoItems"


def test_should_resolve_object_flag_from_in_memory():
    # Given
    return_value = {
        "String": "string",
        "Number": 2,
        "Boolean": True,
    }
    provider = InMemoryProvider(
        {"Key": InMemoryFlag("Key", "obj", {"obj": return_value, "empty": {}})}
    )
    # When
    flag = provider.resolve_object_details(flag_key="Key", default_value={})
    # Then
    assert flag is not None
    assert flag.value == return_value
    assert isinstance(flag.value, dict)
    assert flag.variant == "obj"

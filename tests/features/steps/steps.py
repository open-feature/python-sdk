# flake8: noqa: F811

from behave import given, then, when

from open_feature.evaluation_context import EvaluationContext
from open_feature.exception.error_code import ErrorCode
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.reason import Reason
from open_feature.open_feature_api import get_client, set_provider
from open_feature.open_feature_client import OpenFeatureClient
from open_feature.provider.in_memory_provider import InMemoryProvider
from tests.features.data import IN_MEMORY_FLAGS

# Common step definitions


@then(
    'the resolved {flag_type} details reason of flag with key "{key}" should be '
    '"{reason}"'
)
def step_impl(context, flag_type, key, expected_reason):
    details: FlagEvaluationDetails = None
    if flag_type == "boolean":
        details = context.boolean_flag_details
        assert expected_reason == details.reason.value


@given("a provider is registered with cache disabled")
def step_impl(context):
    set_provider(InMemoryProvider(IN_MEMORY_FLAGS))
    context.client = get_client(name="Default Provider", version="1.0")


@when(
    'a {flag_type} flag with key "{key}" is evaluated with details and default value '
    '"{default_value}"'
)
def step_impl(context, flag_type, key, default_value):
    context.client = get_client(name="Default Provider", version="1.0")
    if flag_type == "boolean":
        context.boolean_flag_details = context.client.get_boolean_details(
            key, default_value
        )
    elif flag_type == "string":
        context.string_flag_details = context.client.get_string_details(
            key, default_value
        )


@when(
    'a boolean flag with key "{key}" is evaluated with {eval_details} and default '
    'value "{default_value}"'
)
def step_impl(context, key, eval_details, default_value):
    client: OpenFeatureClient = context.client

    context.boolean_flag_details = client.get_boolean_details(key, default_value)


@when(
    'a {flag_type} flag with key "{key}" is evaluated with default value '
    '"{default_value}"'
)
def step_impl(context, flag_type, key, default_value):
    client: OpenFeatureClient = context.client

    if flag_type == "boolean":
        context.boolean_flag_details = client.get_boolean_details(key, default_value)
    elif flag_type == "string":
        context.string_flag_details = client.get_string_details(key, default_value)


@then('the resolved string value should be "{expected_value}"')
def step_impl(context, expected_value):
    assert expected_value == context.string_flag_details.value


@then('the resolved boolean value should be "{expected_value}"')
def step_impl(context, expected_value):
    assert parse_boolean(expected_value) == context.boolean_flag_details.value


@when(
    'an integer flag with key "{key}" is evaluated with details and default value '
    "{default_value:d}"
)
def step_impl(context, key, default_value):
    context.flag_key = key
    context.default_value = default_value
    context.integer_flag_details = context.client.get_integer_details(
        key, default_value
    )


@when(
    'an integer flag with key "{key}" is evaluated with default value {default_value:d}'
)
def step_impl(context, key, default_value):
    context.flag_key = key
    context.default_value = default_value
    context.integer_flag_details = context.client.get_integer_details(
        key, default_value
    )


@when('a float flag with key "{key}" is evaluated with default value {default_value:f}')
def step_impl(context, key, default_value):
    context.flag_key = key
    context.default_value = default_value
    context.float_flag_details = context.client.get_float_details(key, default_value)


@when('an object flag with key "{key}" is evaluated with a null default value')
def step_impl(context, key):
    context.flag_key = key
    context.default_value = None
    context.object_flag_details = context.client.get_object_details(key, None)


@then("the resolved integer value should be {expected_value:d}")
def step_impl(context, expected_value):
    assert expected_value == context.integer_flag_details.value


@then("the resolved float value should be {expected_value:f}")
def step_impl(context, expected_value):
    assert expected_value == context.float_flag_details.value


# Flag evaluation step definitions
@then(
    'the resolved boolean details value should be "{expected_value}", the variant '
    'should be "{variant}", and the reason should be "{reason}"'
)
def step_impl(context, expected_value, variant, reason):
    assert parse_boolean(expected_value) == context.boolean_flag_details.value
    assert variant == context.boolean_flag_details.variant
    assert reason == context.boolean_flag_details.reason


@then(
    'the resolved string details value should be "{expected_value}", the variant '
    'should be "{variant}", and the reason should be "{reason}"'
)
def step_impl(context, expected_value, variant, reason):
    assert expected_value == context.string_flag_details.value
    assert variant == context.string_flag_details.variant
    assert reason == context.string_flag_details.reason


@then(
    'the resolved object value should be contain fields "{field1}", "{field2}", and '
    '"{field3}", with values "{val1}", "{val2}" and {val3}, respectively'
)
def step_impl(context, field1, field2, field3, val1, val2, val3):
    value = context.object_flag_details.value
    assert field1 in value
    assert field2 in value
    assert field3 in value
    assert value[field1] == parse_any(val1)
    assert value[field2] == parse_any(val2)
    assert value[field3] == parse_any(val3)


@then('the resolved flag value is "{flag_value}" when the context is empty')
def step_impl(context, flag_value):
    context.string_flag_details = context.client.get_boolean_details(
        context.flag_key, context.default_value
    )
    assert flag_value == context.string_flag_details.value


@then(
    "the reason should indicate an error and the error code should indicate a missing "
    'flag with "{error_code}"'
)
def step_impl(context, error_code):
    assert context.string_flag_details.reason == Reason.ERROR
    assert context.string_flag_details.error_code == ErrorCode[error_code]


@then("the default {flag_type} value should be returned")
def step_impl(context, flag_type):
    flag_details = getattr(context, f"{flag_type}_flag_details")
    assert context.default_value == flag_details.value


@when(
    'a float flag with key "{key}" is evaluated with details and default value '
    "{default_value:f}"
)
def step_impl(context, key, default_value):
    context.float_flag_details = context.client.get_float_details(key, default_value)


@then(
    "the resolved float details value should be {expected_value:f}, the variant should "
    'be "{variant}", and the reason should be "{reason}"'
)
def step_impl(context, expected_value, variant, reason):
    assert expected_value == context.float_flag_details.value
    assert variant == context.float_flag_details.variant
    assert reason == context.float_flag_details.reason


@when(
    'an object flag with key "{key}" is evaluated with details and a null default value'
)
def step_impl(context, key):
    context.object_flag_details = context.client.get_object_details(key, None)


@then(
    'the resolved object details value should be contain fields "{field1}", "{field2}",'
    ' and "{field3}", with values "{val1}", "{val2}" and {val3}, respectively'
)
def step_impl(context, field1, field2, field3, val1, val2, val3):
    value = context.object_flag_details.value
    assert field1 in value
    assert field2 in value
    assert field3 in value
    assert value[field1] == parse_any(val1)
    assert value[field2] == parse_any(val2)
    assert value[field3] == parse_any(val3)


@then('the variant should be "{variant}", and the reason should be "{reason}"')
def step_impl(context, variant, reason):
    assert variant == context.object_flag_details.variant
    assert reason == context.object_flag_details.reason


@when(
    'context contains keys "{key1}", "{key2}", "{key3}", "{key4}" with values "{val1}",'
    ' "{val2}", {val3:d}, "{val4}"'
)
def step_impl(context, key1, key2, key3, key4, val1, val2, val3, val4):
    context.evaluation_context = EvaluationContext(
        None,
        {
            key1: val1,
            key2: val2,
            key3: val3,
            key4: parse_boolean(val4),
        },
    )


@when('a flag with key "{key}" is evaluated with default value "{default_value}"')
def step_impl(context, key, default_value):
    context.flag_key = key
    context.default_value = default_value
    context.string_flag_details = context.client.get_string_details(
        key, default_value, context.evaluation_context
    )


@then('the resolved string response should be "{expected_value}"')
def step_impl(context, expected_value):
    assert expected_value == context.string_flag_details.value


@when(
    'a non-existent string flag with key "{flag_key}" is evaluated with details and a '
    'default value "{default_value}"'
)
def step_impl(context, flag_key, default_value):
    context.flag_key = flag_key
    context.default_value = default_value
    context.string_flag_details = context.client.get_string_details(
        flag_key, default_value
    )


@when(
    'a string flag with key "{flag_key}" is evaluated as an integer, with details and a'
    " default value {default_value:d}"
)
def step_impl(context, flag_key, default_value):
    context.flag_key = flag_key
    context.default_value = default_value
    context.integer_flag_details = context.client.get_integer_details(
        flag_key, default_value
    )


@then(
    "the reason should indicate an error and the error code should indicate a type "
    'mismatch with "{error_code}"'
)
def step_impl(context, error_code):
    assert context.integer_flag_details.reason == Reason.ERROR
    assert context.integer_flag_details.error_code == ErrorCode[error_code]


# Flag caching step definitions


@given(
    'the flag\'s configuration with key "{key}" is updated to defaultVariant '
    '"{variant}"'
)
def step_impl(context, key, variant):
    raise NotImplementedError("Step definition not implemented yet")


@given("sleep for {duration} milliseconds")
def step_impl(context, duration):
    raise NotImplementedError("Step definition not implemented yet")


@then('the resolved string details reason should be "{reason}"')
def step_impl(context, reason):
    raise NotImplementedError("Step definition not implemented yet")


@then(
    "the resolved integer details value should be {expected_value:d}, the variant "
    'should be "{variant}", and the reason should be "{reason}"'
)
def step_impl(context, expected_value, variant, reason):
    assert expected_value == context.integer_flag_details.value
    assert variant == context.integer_flag_details.variant
    assert reason == context.integer_flag_details.reason


def parse_boolean(value):
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def parse_any(value):
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    if value.isdigit():
        return int(value)
    return value

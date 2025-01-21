from behave import given, then

from openfeature.api import get_client, set_provider
from openfeature.provider.in_memory_provider import InMemoryProvider
from tests.features.data import IN_MEMORY_FLAGS


@given("a stable provider")
def step_impl_stable_provider(context):
    set_provider(InMemoryProvider(IN_MEMORY_FLAGS))
    context.client = get_client()


@then('the resolved metadata value "{key}" should be "{value}"')
def step_impl_check_metadata(context, key, value):
    assert context.evaluation.flag_metadata[key] == value


@then("the resolved metadata is empty")
def step_impl_empty_metadata(context):
    assert not context.evaluation.flag_metadata


@then("the resolved metadata should contain")
def step_impl_metadata_contains(context):
    for row in context.table:
        key, metadata_type, value = row

        assert context.evaluation.flag_metadata[
           key
       ] == convert_value_from_metadata_type(value, metadata_type)


def convert_value_from_metadata_type(value, metadata_type):
    if value == "None":
        return None
    if metadata_type.lower() == "boolean":
        return bool(value)
    elif metadata_type.lower() == "integer":
        return int(value)
    elif metadata_type.lower() == "float":
        return float(value)
    return value

from behave import given, then, when

from openfeature.api import get_client, set_provider
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import ErrorCode
from openfeature.flag_evaluation import FlagEvaluationDetails, Reason
from openfeature.provider.in_memory_provider import InMemoryProvider
from tests.features.data import IN_MEMORY_FLAGS

@given("a stable provider")
def step_impl(context):
    set_provider(InMemoryProvider(IN_MEMORY_FLAGS))
    context.client = get_client()

@then('the resolved metadata value "{key}" should be "{value}"')
def step_impl(context, key, value):
    assert context.evaluation.metadata[key] == value



@then("the resolved metadata is empty")
def step_impl(context):
    assert context.evaluation.metadata


@then("the resolved metadata should contain")
def step_impl(context):


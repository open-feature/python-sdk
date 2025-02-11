from unittest.mock import MagicMock

from behave import given, then

from openfeature.exception import ErrorCode
from openfeature.flag_evaluation import Reason
from openfeature.hook import Hook


@given("a client with added hook")
def step_impl_add_hook(context):
    hook = MagicMock(spec=Hook)
    hook.before = MagicMock()
    hook.after = MagicMock()
    hook.error = MagicMock()
    hook.finally_after = MagicMock()
    context.hook = hook
    context.client.add_hooks([hook])


@then('the "{hook_name}" hook should have been executed')
def step_impl_should_called(context, hook_name):
    hook = get_hook_from_name(context, hook_name)
    assert hook.called


@then('the "{hook_names}" hooks should be called with evaluation details')
def step_impl_should_have_eval_details(context, hook_names):
    for hook_name in hook_names.split(", "):
        hook = get_hook_from_name(context, hook_name)
        for row in context.table:
            flag_type, key, value = row

            value = convert_value_from_key_and_flag_type(value, key, flag_type)
            actual = hook.call_args[1]["details"].__dict__[key]

            assert actual == value


def get_hook_from_name(context, hook_name):
    if hook_name.lower() == "before":
        return context.hook.before
    elif hook_name.lower() == "after":
        return context.hook.after
    elif hook_name.lower() == "error":
        return context.hook.error
    elif hook_name.lower() == "finally":
        return context.hook.finally_after
    else:
        raise ValueError(str(hook_name) + " is not a valid hook name")


def convert_value_from_key_and_flag_type(value, key, flag_type):
    if value in ("None", "null"):
        return None
    if flag_type.lower() == "boolean":
        return bool(value)
    elif flag_type.lower() == "integer":
        return int(value)
    elif flag_type.lower() == "float":
        return float(value)
    elif key == "reason":
        return Reason(value)
    elif key == "error_code":
        return ErrorCode(value)
    return value

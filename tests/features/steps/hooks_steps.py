from unittest.mock import MagicMock

from behave import then, when

from openfeature.exception import ErrorCode
from openfeature.hook import Hook


@when('a hook is added to the client')
def step_impl_add_hook(context):
    hook = MagicMock(spec=Hook)
    hook.before = MagicMock()
    hook.after = MagicMock()
    hook.error = MagicMock()
    hook.finally_after = MagicMock()
    context.hook = hook
    context.client.add_hooks([hook])


@then('error hooks should be called')
def step_impl_call_error(context):
    assert context.hook.before.called
    assert context.hook.error.called
    assert context.hook.finally_after.called


@then('non-error hooks should be called')
def step_impl_call_non_error(context):
    assert context.hook.before.called
    assert context.hook.after.called
    assert context.hook.finally_after.called


def get_hook_from_name(context, hook_name):
    if hook_name.lower() == 'before':
        return context.hook.before
    elif hook_name.lower() == 'after':
        return context.hook.after
    elif hook_name.lower() == 'error':
        return context.hook.error
    elif hook_name.lower() == 'finally':
        return context.hook.finally_after
    else:
        raise ValueError(str(hook_name) + ' is not a valid hook name')


def convert_value_from_flag_type(value, flag_type):
    if value == 'None':
        return None
    if flag_type.lower() == 'boolean':
        return bool(value)
    elif flag_type.lower() == 'integer':
        return int(value)
    elif flag_type.lower() == 'float':
        return float(value)
    return value

@then('"{hook_names}" hooks should have evaluation details')
def step_impl_should_have_eval_details(context, hook_names):
    for hook_name in hook_names.split(', '):
        hook = get_hook_from_name(context, hook_name)
        for row in context.table:
            flag_type, key, value = row

            value = convert_value_from_flag_type(value, flag_type)

            actual = hook.call_args[1]['details'].__dict__[key]
            if isinstance(actual, ErrorCode):
                actual = str(actual)

            assert actual == value

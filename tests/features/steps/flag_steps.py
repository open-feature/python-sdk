from behave import given, then, when


@given('a {flag_type}-flag with key "{flag_key}" and a default value "{default_value}"')
def step_impl(context, flag_type: str, flag_key, default_value):
    context.flag = (flag_type, flag_key, default_value)


@when("the flag was evaluated with details")
def step_impl(context):
    client = context.client
    flag_type, key, default_value = context.flag
    if flag_type.lower() == "string":
        context.evaluation = client.get_string_details(key, default_value)
    elif flag_type.lower() == "boolean":
        context.evaluation = client.get_boolean_details(key, default_value)
    elif flag_type.lower() == "object":
        context.evaluation = client.get_object_details(key, default_value)
    elif flag_type.lower() == "float":
        context.evaluation = client.get_float_details(key, default_value)
    elif flag_type.lower() == "integer":
        context.evaluation = client.get_integer_details(key, default_value)

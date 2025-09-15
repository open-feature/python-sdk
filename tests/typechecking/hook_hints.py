"""Requirement 4.1.2"""

from datetime import datetime

from openfeature.hook import HookHints

# positive
bool_hook_hint: HookHints = {"bool": True}

int_hook_hint: HookHints = {"int": 42}

float_hook_hint: HookHints = {"float": 3.14}

str_hook_hint: HookHints = {"str": "value"}

date_hook_hint: HookHints = {"date": datetime.now()}

list_hook_hint: HookHints = {
    "bool_list": [True, False],
    "int_list": [1, 2],
    "float_list": [1.1, 2.2],
    "date_list": [datetime.now(), datetime.now()],
    "str_list": ["a", "b"],
    "list_list": [
        ["a", "b"],
        ["c", "d"],
    ],
    "dict_list": [
        {"int": 42},
        {"str": "value"},
    ],
}

dict_hook_hint: HookHints = {
    "user": {
        "id": 12345,
        "name": "John Doe",
        "active": True,
        "last_login": datetime.now(),
        "permissions": ["read", "write", "admin"],
        "metadata": {
            "source": "api",
            "version": 2.1,
            "tags": ["premium", "beta"],
            "config": {
                "nested_deeply": [
                    {"item": 1, "enabled": True},
                    {"item": 2, "enabled": False},
                ]
            },
        },
    },
}

# negative
null_hook_hint: HookHints = {"null": None}  # type: ignore[dict-item]

complex_hook_hint: HookHints = {"complex": -4.5j}  # type: ignore[dict-item]

int_key_hook_hint: HookHints = {42: 42}  # type: ignore[dict-item]

"""Requirement 4.6.1"""

from openfeature.hook import HookData

# positive
any_hook_data: HookData = {
    "user": {
        "id": 12345,
        "name": "John Doe",
        "active": True,
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


class ExampleClass:
    pass


class_hook_data: HookData = {"example": ExampleClass}

# negative
int_key_hook_data: HookData = {42: 42}  # ty: ignore[invalid-assignment]

"""Requirement 3.1.2"""

from datetime import datetime

from openfeature.evaluation_context import EvaluationContext

# positive
EvaluationContext(
    targeting_key="key",
    attributes={"bool": True},
)

EvaluationContext(
    targeting_key="key",
    attributes={"int": 42},
)

EvaluationContext(
    targeting_key="key",
    attributes={"float": 3.14},
)

EvaluationContext(
    targeting_key="key",
    attributes={"str": "value"},
)

EvaluationContext(
    targeting_key="key",
    attributes={"date": datetime.now()},
)

EvaluationContext(
    targeting_key="key",
    attributes={
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
    },
)

EvaluationContext(
    targeting_key="key",
    attributes={
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
    },
)

# negative
EvaluationContext(
    targeting_key="key",
    attributes={"null": None},  # type: ignore[dict-item]
)

EvaluationContext(
    targeting_key="key",
    attributes={"complex": -4.5j},  # type: ignore[dict-item]
)

EvaluationContext(
    targeting_key="key",
    attributes={42: 42},  # type: ignore[dict-item]
)

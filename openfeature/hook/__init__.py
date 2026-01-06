from __future__ import annotations

import typing
from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime
from enum import Enum

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType, FlagValueType

if typing.TYPE_CHECKING:
    from openfeature.client import ClientMetadata
    from openfeature.provider.metadata import Metadata

__all__ = [
    "Hook",
    "HookContext",
    "HookData",
    "HookHints",
    "HookType",
    "add_hooks",
    "clear_hooks",
    "get_hooks",
]

_hooks: list[Hook] = []


# https://openfeature.dev/specification/sections/hooks/#requirement-461
HookData = MutableMapping[str, typing.Any]


class HookType(Enum):
    BEFORE = "before"
    AFTER = "after"
    FINALLY_AFTER = "finally_after"
    ERROR = "error"


class HookContext:
    def __init__(  # noqa: PLR0913
        self,
        flag_key: str,
        flag_type: FlagType,
        default_value: FlagValueType,
        evaluation_context: EvaluationContext,
        client_metadata: ClientMetadata | None = None,
        provider_metadata: Metadata | None = None,
        hook_data: HookData | None = None,
    ):
        self.flag_key = flag_key
        self.flag_type = flag_type
        self.default_value = default_value
        self.evaluation_context = evaluation_context
        self.client_metadata = client_metadata
        self.provider_metadata = provider_metadata
        self.hook_data = hook_data or {}

    def __setattr__(self, key: str, value: typing.Any) -> None:
        if hasattr(self, key) and key in (
            "flag_key",
            "flag_type",
            "default_value",
            "client_metadata",
            "provider_metadata",
        ):
            raise AttributeError(f"Attribute {key!r} is immutable")
        super().__setattr__(key, value)


# https://openfeature.dev/specification/sections/hooks/#requirement-421
HookHintValue = (
    bool
    | int
    | float
    | str
    | datetime
    | Sequence["HookHintValue"]
    | Mapping[str, "HookHintValue"]
)

HookHints = Mapping[str, HookHintValue]


class Hook:
    def before(
        self, hook_context: HookContext, hints: HookHints
    ) -> EvaluationContext | None:
        """
        Runs before flag is resolved.

        :param hook_context: Information about the particular flag evaluation
        :param hints: An immutable mapping of data for users to
        communicate to the hooks.
        :return: An EvaluationContext. It will be merged with the
        EvaluationContext instances from other hooks, the client and API.
        """
        return None

    def after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[FlagValueType],
        hints: HookHints,
    ) -> None:
        """
        Runs after a flag is resolved.

        :param hook_context: Information about the particular flag evaluation
        :param details: Information about how the flag was resolved,
        including any resolved values.
        :param hints: A mapping of data for users to communicate to the hooks.
        """
        pass

    def error(
        self, hook_context: HookContext, exception: Exception, hints: HookHints
    ) -> None:
        """
        Run when evaluation encounters an error. Errors thrown will be swallowed.

        :param hook_context: Information about the particular flag evaluation
        :param exception: The exception that was thrown
        :param hints: A mapping of data for users to communicate to the hooks.
        """
        pass

    def finally_after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[FlagValueType],
        hints: HookHints,
    ) -> None:
        """
        Run after flag evaluation, including any error processing.
        This will always run. Errors will be swallowed.

        :param hook_context: Information about the particular flag evaluation
        :param hints: A mapping of data for users to communicate to the hooks.
        """
        pass

    def supports_flag_value_type(self, flag_type: FlagType) -> bool:
        """
        Check to see if the hook supports the particular flag type.

        :param flag_type: particular type of the flag
        :return: a boolean containing whether the flag type is supported (True)
        or not (False)
        """
        return True


def add_hooks(hooks: list[Hook]) -> None:
    global _hooks
    _hooks = _hooks + hooks


def clear_hooks() -> None:
    global _hooks
    _hooks = []


def get_hooks() -> list[Hook]:
    return _hooks

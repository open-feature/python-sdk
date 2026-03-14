from __future__ import annotations

import logging
import typing
from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime
from enum import Enum

from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import ErrorCode, OpenFeatureError
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
    "LoggingHook",
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
HookHintValue: typing.TypeAlias = (
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


class LoggingHook(Hook):
    def __init__(
        self,
        include_evaluation_context: bool = False,
        logger: logging.Logger | None = None,
    ):
        self.logger = logger or logging.getLogger("openfeature")
        self.include_evaluation_context = include_evaluation_context

    def _build_args(self, hook_context: HookContext) -> dict:
        args = {
            "domain": hook_context.client_metadata.domain
            if hook_context.client_metadata
            else None,
            "provider_name": hook_context.provider_metadata.name
            if hook_context.provider_metadata
            else None,
            "flag_key": hook_context.flag_key,
            "default_value": hook_context.default_value,
        }
        if self.include_evaluation_context:
            args["evaluation_context"] = {
                "targeting_key": hook_context.evaluation_context.targeting_key,
                "attributes": hook_context.evaluation_context.attributes,
            }
        return args

    def before(
        self, hook_context: HookContext, hints: HookHints
    ) -> EvaluationContext | None:
        args = self._build_args(hook_context)
        args["stage"] = "before"
        self.logger.debug("Before stage %s", args)
        return None

    def after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[FlagValueType],
        hints: HookHints,
    ) -> None:
        args = self._build_args(hook_context)
        extra_args = {
            "stage": "after",
            "reason": details.reason,
            "variant": details.variant,
            "value": details.value,
        }
        self.logger.debug("After stage %s", {**args, **extra_args})

    def error(
        self, hook_context: HookContext, exception: Exception, hints: HookHints
    ) -> None:
        args = self._build_args(hook_context)
        extra_args = {
            "stage": "error",
            "error_code": exception.error_code if isinstance(exception, OpenFeatureError) else ErrorCode.GENERAL,
            "error_message": str(exception),
        }
        self.logger.error("Error stage %s", {**args, **extra_args})

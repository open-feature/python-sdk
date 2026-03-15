import json
import logging
from dataclasses import asdict

from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import ErrorCode, OpenFeatureError
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagValueType
from openfeature.hook import Hook, HookContext, HookHints


class LoggingHook(Hook):
    def __init__(
        self,
        include_evaluation_context: bool = False,
        logger: logging.Logger | None = None,
    ):
        self.logger = logger or logging.getLogger("openfeature")
        self.include_evaluation_context = include_evaluation_context

    def _build_args(self, hook_context: HookContext, stage: str) -> dict:
        args = {
            "domain": hook_context.client_metadata.domain
            if hook_context.client_metadata
            else None,
            "provider_name": hook_context.provider_metadata.name
            if hook_context.provider_metadata
            else None,
            "flag_key": hook_context.flag_key,
            "default_value": hook_context.default_value,
            "stage": stage,
        }
        if self.include_evaluation_context:
            args["evaluation_context"] = json.dumps(
                asdict(hook_context.evaluation_context),
                default=str,
            )
        return args

    def before(
        self, hook_context: HookContext, hints: HookHints
    ) -> EvaluationContext | None:
        args = self._build_args(hook_context, "before")
        self.logger.debug("Flag evaluation %s", args)
        return None

    def after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[FlagValueType],
        hints: HookHints,
    ) -> None:
        args = self._build_args(hook_context, "after")
        args["reason"] = details.reason
        args["variant"] = details.variant
        args["value"] = details.value
        self.logger.debug("Flag evaluation %s", args)

    def error(
        self, hook_context: HookContext, exception: Exception, hints: HookHints
    ) -> None:
        args = self._build_args(hook_context, "error")
        args["error_code"] = (
            exception.error_code
            if isinstance(exception, OpenFeatureError)
            else ErrorCode.GENERAL
        )
        args["error_message"] = str(exception)
        self.logger.error("Flag evaluation %s", args)

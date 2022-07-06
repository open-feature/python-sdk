from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook import Hook
from open_feature.hooks.hook_context import HookContext


def error_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    exception: Exception,
    hooks: list,
    hints: dict,
):
    execute_hooks(flag_type, hooks, "error", Hook.error(hook_context, exception, hints))


def after_all_hooks(
    flag_type: FlagType, hook_context: HookContext, hooks: list, hints: dict
):
    execute_hooks(flag_type, hooks, "finally", Hook.finally_after(hook_context, hints))


def after_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    details: FlagEvaluationDetails,
    hooks: list,
    hints: dict,
):
    execute_hooks_unchecked(flag_type, hooks, Hook.after(hook_context, details, hints))


def before_hooks(
    flag_type: FlagType, hook_context: HookContext, hooks: list, hints: dict
):
    pass


def execute_hooks(flag_type: FlagType, hooks: list, hook_method: str, param1):
    pass


def execute_hooks_unchecked(flag_type, hooks, param):
    pass

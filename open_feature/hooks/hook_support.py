import logging
from functools import reduce

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook import Hook
from open_feature.hooks.hook_context import HookContext


def error_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    exception: Exception,
    hooks: list[Hook],
    hints: dict,
):
    kwargs = {"ctx": hook_context, "exception": exception, "hints": hints}
    execute_hooks(flag_type=flag_type, hooks=hooks, hook_method="error", **kwargs)


def after_all_hooks(
    flag_type: FlagType, hook_context: HookContext, hooks: list, hints: dict
):
    kwargs = {"ctx": hook_context, "hints": hints}
    execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method="finally_after", **kwargs
    )


def after_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    details: FlagEvaluationDetails,
    hooks: list[Hook],
    hints: dict,
):
    kwargs = {"ctx": hook_context, "details": details, "hints": hints}
    execute_hooks_unchecked(
        flag_type=flag_type, hooks=hooks, hook_method="after", **kwargs
    )


def before_hooks(
    flag_type: FlagType, hook_context: HookContext, hooks: list[Hook], hints: dict
) -> EvaluationContext:
    kwargs = {"ctx": hook_context, "hints": hints}
    executed_hooks = execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method="before", **kwargs
    )
    filtered_hooks = list(filter(lambda hook: hook is None, executed_hooks))

    if filtered_hooks:
        return reduce(lambda a, b: a.merge(b), filtered_hooks)
    else:
        return EvaluationContext()


def execute_hooks(
    flag_type: FlagType, hooks: list[Hook], hook_method: str, **kwargs
) -> list:
    if hooks:
        filtered_hooks = list(
            filter(
                lambda hook: hook.supports_flag_value_type(flag_type=flag_type), hooks
            )
        )
        return [execute_checked(hook, hook_method, **kwargs) for hook in filtered_hooks]
    return []


def execute_hooks_unchecked(
    flag_type: FlagType, hooks, hook_method: str, **kwargs
) -> list:
    if hooks:
        filtered_hooks = list(
            filter(
                lambda hook: hook.supports_flag_value_type(flag_type=flag_type), hooks
            )
        )
        return [getattr(hook, hook_method)(**kwargs) for hook in filtered_hooks]


def execute_checked(hook: Hook, hook_method: str, **kwargs):
    try:
        getattr(hook, hook_method)(**kwargs)
    except Exception:
        logging.error(f"Exception when running {hook_method} hooks")

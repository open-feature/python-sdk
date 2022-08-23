import logging
import typing
from functools import reduce

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook import Hook
from open_feature.hooks.hook_context import HookContext
from open_feature.hooks.hook_type import HookType


def error_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    exception: Exception,
    hooks: typing.List[Hook],
    hints: dict,
):
    """

    :param flag_type:
    :param hook_context:
    :param exception:
    :param hooks:
    :param hints:
    :return:
    """
    kwargs = {"ctx": hook_context, "exception": exception, "hints": hints}
    _execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.ERROR, **kwargs
    )


def after_all_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    hooks: typing.List[Hook],
    hints: dict,
):
    """

    :param flag_type:
    :param hook_context:
    :param hooks:
    :param hints:
    :return:
    """
    kwargs = {"ctx": hook_context, "hints": hints}
    _execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.FINALLY_AFTER, **kwargs
    )


def after_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    details: FlagEvaluationDetails,
    hooks: typing.List[Hook],
    hints: dict,
):
    """

    :param flag_type:
    :param hook_context:
    :param details:
    :param hooks:
    :param hints:
    :return:
    """
    kwargs = {"ctx": hook_context, "details": details, "hints": hints}
    _execute_hooks_unchecked(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.AFTER, **kwargs
    )


def before_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    hooks: typing.List[Hook],
    hints: dict,
) -> EvaluationContext:
    kwargs = {"ctx": hook_context, "hints": hints}
    executed_hooks = _execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.BEFORE, **kwargs
    )
    filtered_hooks = list(filter(lambda hook: hook is not None, executed_hooks))

    if filtered_hooks:
        return reduce(lambda a, b: a.merge(b), filtered_hooks)

    return EvaluationContext()


def _execute_hooks(
    flag_type: FlagType, hooks: typing.List[Hook], hook_method: HookType, **kwargs
) -> list:
    if hooks:
        filtered_hooks = list(
            filter(
                lambda hook: hook.supports_flag_value_type(flag_type=flag_type), hooks
            )
        )
        return [
            _execute_checked(hook, hook_method, **kwargs) for hook in filtered_hooks
        ]
    return []


def _execute_hooks_unchecked(
    flag_type: FlagType, hooks, hook_method: HookType, **kwargs
) -> list:
    if hooks:
        filtered_hooks = list(
            filter(
                lambda hook: hook.supports_flag_value_type(flag_type=flag_type), hooks
            )
        )
        return [getattr(hook, hook_method.value)(**kwargs) for hook in filtered_hooks]

    return []


def _execute_checked(hook: Hook, hook_method: HookType, **kwargs):
    try:
        getattr(hook, hook_method.value)(**kwargs)
    except Exception:
        logging.error(f"Exception when running {hook_method.value} hooks")

import logging
import typing
from functools import reduce

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType
from openfeature.hook import Hook, HookContext, HookType

logger = logging.getLogger("openfeature")


def error_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    exception: Exception,
    hooks: typing.List[Hook],
    hints: typing.Optional[typing.Mapping] = None,
) -> None:
    kwargs = {"hook_context": hook_context, "exception": exception, "hints": hints}
    _execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.ERROR, **kwargs
    )


def after_all_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    hooks: typing.List[Hook],
    hints: typing.Optional[typing.Mapping] = None,
) -> None:
    kwargs = {"hook_context": hook_context, "hints": hints}
    _execute_hooks(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.FINALLY_AFTER, **kwargs
    )


def after_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    details: FlagEvaluationDetails[typing.Any],
    hooks: typing.List[Hook],
    hints: typing.Optional[typing.Mapping] = None,
) -> None:
    kwargs = {"hook_context": hook_context, "details": details, "hints": hints}
    _execute_hooks_unchecked(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.AFTER, **kwargs
    )


def before_hooks(
    flag_type: FlagType,
    hook_context: HookContext,
    hooks: typing.List[Hook],
    hints: typing.Optional[typing.Mapping] = None,
) -> EvaluationContext:
    kwargs = {"hook_context": hook_context, "hints": hints}
    executed_hooks = _execute_hooks_unchecked(
        flag_type=flag_type, hooks=hooks, hook_method=HookType.BEFORE, **kwargs
    )
    filtered_hooks = [result for result in executed_hooks if result is not None]

    if filtered_hooks:
        return reduce(lambda a, b: a.merge(b), filtered_hooks)

    return EvaluationContext()


def _execute_hooks(
    flag_type: FlagType,
    hooks: typing.List[Hook],
    hook_method: HookType,
    **kwargs: typing.Any,
) -> list:
    """
    Run multiple hooks of any hook type. All of these hooks will be run through an
    exception check.

    :param flag_type: particular type of flag
    :param hooks: a list of hooks
    :param hook_method: the type of hook that is being run
    :param kwargs: arguments that need to be provided to the hook method
    :return: a list of results from the applied hook methods
    """
    return [
        _execute_hook_checked(hook, hook_method, **kwargs)
        for hook in hooks
        if hook.supports_flag_value_type(flag_type)
    ]


def _execute_hooks_unchecked(
    flag_type: FlagType,
    hooks: typing.List[Hook],
    hook_method: HookType,
    **kwargs: typing.Any,
) -> typing.List[typing.Optional[EvaluationContext]]:
    """
    Execute a single hook without checking whether an exception is thrown. This is
    used in the before and after hooks since any exception will be caught in the
    client.

    :param flag_type: particular type of flag
    :param hooks: a list of hooks
    :param hook_method: the type of hook that is being run
    :param kwargs: arguments that need to be provided to the hook method
    :return: a list of results from the applied hook methods
    """
    return [
        getattr(hook, hook_method.value)(**kwargs)
        for hook in hooks
        if hook.supports_flag_value_type(flag_type)
    ]


def _execute_hook_checked(
    hook: Hook, hook_method: HookType, **kwargs: typing.Any
) -> typing.Optional[EvaluationContext]:
    """
    Try and run a single hook and catch any exception thrown. This is used in the
    after all and error hooks since any error thrown at this point needs to be caught.

    :param hook: a list of hooks
    :param hook_method: the type of hook that is being run
    :param kwargs: arguments that need to be provided to the hook method
    :return: the result of the hook method
    """
    try:
        return typing.cast(
            "typing.Optional[EvaluationContext]",
            getattr(hook, hook_method.value)(**kwargs),
        )
    except Exception:  # pragma: no cover
        logger.exception(f"Exception when running {hook_method.value} hooks")
        return None

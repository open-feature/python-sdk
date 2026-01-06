import logging
import typing
from functools import reduce

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagType
from openfeature.hook import Hook, HookContext, HookHints, HookType

logger = logging.getLogger("openfeature")


def error_hooks(
    flag_type: FlagType,
    exception: Exception,
    hooks_and_context: list[tuple[Hook, HookContext]],
    hints: HookHints | None = None,
) -> None:
    kwargs = {"exception": exception, "hints": hints}
    _execute_hooks(
        flag_type=flag_type,
        hooks_and_context=hooks_and_context,
        hook_method=HookType.ERROR,
        **kwargs,
    )


def after_all_hooks(
    flag_type: FlagType,
    details: FlagEvaluationDetails[typing.Any],
    hooks_and_context: list[tuple[Hook, HookContext]],
    hints: HookHints | None = None,
) -> None:
    kwargs = {"details": details, "hints": hints}
    _execute_hooks(
        flag_type=flag_type,
        hooks_and_context=hooks_and_context,
        hook_method=HookType.FINALLY_AFTER,
        **kwargs,
    )


def after_hooks(
    flag_type: FlagType,
    details: FlagEvaluationDetails[typing.Any],
    hooks_and_context: list[tuple[Hook, HookContext]],
    hints: HookHints | None = None,
) -> None:
    kwargs = {"details": details, "hints": hints}
    _execute_hooks_unchecked(
        flag_type=flag_type,
        hooks_and_context=hooks_and_context,
        hook_method=HookType.AFTER,
        **kwargs,
    )


def before_hooks(
    flag_type: FlagType,
    hooks_and_context: list[tuple[Hook, HookContext]],
    hints: HookHints | None = None,
) -> EvaluationContext:
    kwargs = {"hints": hints}
    executed_hooks = _execute_hooks_unchecked(
        flag_type=flag_type,
        hooks_and_context=hooks_and_context,
        hook_method=HookType.BEFORE,
        **kwargs,
    )
    filtered_hooks = [result for result in executed_hooks if result is not None]

    if filtered_hooks:
        return reduce(lambda a, b: a.merge(b), filtered_hooks)

    return EvaluationContext()


def _execute_hooks(
    flag_type: FlagType,
    hooks_and_context: list[tuple[Hook, HookContext]],
    hook_method: HookType,
    **kwargs: typing.Any,
) -> list[EvaluationContext | None]:
    """
    Run multiple hooks of any hook type. All of these hooks will be run through an
    exception check.

    :param flag_type: particular type of flag
    :param hooks_and_context: a list of hooks and their context
    :param hook_method: the type of hook that is being run
    :param kwargs: arguments that need to be provided to the hook method
    :return: a list of results from the applied hook methods
    """
    return [
        _execute_hook_checked(hook, hook_method, hook_context=hook_context, **kwargs)
        for (hook, hook_context) in hooks_and_context
        if hook.supports_flag_value_type(flag_type)
    ]


def _execute_hooks_unchecked(
    flag_type: FlagType,
    hooks_and_context: list[tuple[Hook, HookContext]],
    hook_method: HookType,
    **kwargs: typing.Any,
) -> list[EvaluationContext | None]:
    """
    Execute a single hook without checking whether an exception is thrown. This is
    used in the before and after hooks since any exception will be caught in the
    client.

    :param flag_type: particular type of flag
    :param hooks_and_context: a list of hooks and their context
    :param hook_method: the type of hook that is being run
    :param kwargs: arguments that need to be provided to the hook method
    :return: a list of results from the applied hook methods
    """
    return [
        getattr(hook, hook_method.value)(hook_context=hook_context, **kwargs)
        for (hook, hook_context) in hooks_and_context
        if hook.supports_flag_value_type(flag_type)
    ]


def _execute_hook_checked(
    hook: Hook, hook_method: HookType, **kwargs: typing.Any
) -> EvaluationContext | None:
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
            "EvaluationContext | None",
            getattr(hook, hook_method.value)(**kwargs),
        )
    except Exception:  # pragma: no cover
        logger.exception(f"Exception when running {hook_method.value} hooks")
        return None

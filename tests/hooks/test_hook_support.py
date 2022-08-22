from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook import Hook
from open_feature.hooks.hook_context import HookContext
from open_feature.hooks.hook_support import error_hooks
from tests.hooks.conftest import TestHook


def setup():
    test_hook = TestHook()
    assert isinstance(test_hook, Hook)


def test_error_hooks_run_error_method(test_hook):
    # Given
    hook_context = HookContext("flag_key", FlagType.BOOLEAN, True, "")
    # When
    error_hooks(FlagType.BOOLEAN, hook_context, Exception, [test_hook], {})
    # Then
    assert True

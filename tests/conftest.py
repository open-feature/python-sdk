import pytest

from open_feature import open_feature_api as api
from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.exceptions import OpenFeatureError
from open_feature.flag_evaluation.error_code import ErrorCode
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook import Hook
from open_feature.hooks.hook_context import HookContext
from open_feature.provider.no_op_provider import NoOpProvider


@pytest.fixture(autouse=True)
def clear_provider():
    yield
    # Setting private provider back to None to ensure other tests aren't affected
    _provider = None  # noqa: F841


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()


class TestExceptionHook(Hook):
    def before(self, hook_context: HookContext, hints: dict) -> EvaluationContext:
        pass

    def after(
        self, hook_context: HookContext, details: FlagEvaluationDetails, hints: dict
    ):
        raise Exception("Generic exception raised")

    def error(self, hook_context: HookContext, exception: Exception, hints: dict):
        pass

    def finally_after(self, hook_context: HookContext, hints: dict):
        pass

    def supports_flag_value_type(self, flag_type: FlagType) -> bool:
        return True


class TestOpenFeatureErrorHook(Hook):
    def before(self, hook_context: HookContext, hints: dict) -> EvaluationContext:
        pass

    def after(
        self, hook_context: HookContext, details: FlagEvaluationDetails, hints: dict
    ):
        raise OpenFeatureError("error_message", ErrorCode.GENERAL)

    def error(self, hook_context: HookContext, exception: Exception, hints: dict):
        pass

    def finally_after(self, hook_context: HookContext, hints: dict):
        pass

    def supports_flag_value_type(self, flag_type: FlagType) -> bool:
        return True

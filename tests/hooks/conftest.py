import pytest

from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook import Hook


class TestHook(Hook):
    def before(self, ctx, hints: dict):
        pass

    def after(self, ctx, details: FlagEvaluationDetails, hints: dict):
        pass

    def error(self, ctx, exception: Exception, hints: dict):
        return "Error"

    def finally_after(self, ctx, hints: dict):
        pass

    def supports_flag_value_type(self, flag_type: FlagType) -> bool:
        return True


@pytest.fixture()
def test_hook():
    return TestHook()

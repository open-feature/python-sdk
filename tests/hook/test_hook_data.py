import typing

from openfeature.api import set_provider
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagEvaluationDetails, FlagValueType
from openfeature.hook import Hook, HookContext, HookHints
from openfeature.provider.no_op_provider import NoOpProvider


class Example:
    def __init__(self):
        self.value = "example"


class HookWithData(Hook):
    def __init__(self, data: dict[str, typing.Any]):
        self.data_before = data
        self.data_after = None

    def before(
        self, hook_context: HookContext, hints: HookHints
    ) -> typing.Optional[EvaluationContext]:
        hook_context.hook_data = hook_context.hook_data | self.data_before
        return None

    def after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[FlagValueType],
        hints: HookHints,
    ) -> None:
        self.data_after = hook_context.hook_data


def test_hook_data_is_not_shared_between_hooks():
    """Requirement

    4.3.2 - "Hook data" MUST must be created before the first "stage" invoked in a hook for a specific evaluation
            and propagated between each "stage" of the hook. The hook data is not shared between different hooks.
    4.6.1 - "Hook data" MUST be a structure supporting the definition of arbitrary properties, with keys of type string,
            and values of any type.
    """

    # given
    provider = NoOpProvider()
    set_provider(provider)

    client = OpenFeatureClient(domain=None, version=None)

    hook_1 = HookWithData({"key": "value"})
    hook_2 = HookWithData({"key": Example()})
    client.add_hooks([hook_1, hook_2])

    # when
    client.get_boolean_value(flag_key="test-flag", default_value=False)

    # then
    assert hook_1.data_after["key"] == "value"
    assert isinstance(hook_2.data_after["key"], Example)
    assert hook_2.data_after["key"].value == "example"

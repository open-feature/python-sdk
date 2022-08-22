from abc import abstractmethod

from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.flag_type import FlagType
from open_feature.hooks.hook_context import HookContext


class Hook:
    @abstractmethod
    def before(self, hook_context: HookContext, hints: dict) -> EvaluationContext:
        """
        Runs before flag is resolved.

        :param hook_context: Information about the particular flag evaluation
        :param hints: An immutable mapping of data for users to
        communicate to the hooks.
        :return: An optional EvaluationContext. If returned, it will
        be merged with the EvaluationContext instances from other
        hooks, the client and API.
        """
        pass

    @abstractmethod
    def after(
        self, hook_context: HookContext, details: FlagEvaluationDetails, hints: dict
    ):
        """
        Runs after a flag is resolved.

        :param hook_context: Information about the particular flag evaluation
        :param details: Information about how the flag was resolved,
        including any resolved values.
        :param hints: An immutable mapping of data for users to
        communicate to the hooks.
        """
        pass

    @abstractmethod
    def error(self, hook_context: HookContext, exception: Exception, hints: dict):
        """
        Run when evaluation encounters an error. This will always run.
        Errors thrown will be swallowed.

        :param hook_context: Information about the particular flag evaluation
        :param exception:
        :param hints: An immutable mapping of data for users to
        communicate to the hooks.
        """
        pass

    @abstractmethod
    def finally_after(self, hook_context: HookContext, hints: dict):
        """
        Run after flag evaluation, including any error processing.
        This will always run. Errors will be swallowed.

        :param hook_context: Information about the particular flag evaluation
        :param hints: An immutable mapping of data for users to
        communicate to the hooks.
        """
        pass

    @abstractmethod
    def supports_flag_value_type(self, flag_type: FlagType) -> bool:
        return True

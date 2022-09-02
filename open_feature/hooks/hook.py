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
        :return: An EvaluationContext. It will be merged with the
        EvaluationContext instances from other hooks, the client and API.
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
        :param hints: A mapping of data for users to communicate to the hooks.
        """
        pass

    @abstractmethod
    def error(self, hook_context: HookContext, exception: Exception, hints: dict):
        """
        Run when evaluation encounters an error. Errors thrown will be swallowed.

        :param hook_context: Information about the particular flag evaluation
        :param exception: The exception that was thrown
        :param hints: A mapping of data for users to communicate to the hooks.
        """
        pass

    @abstractmethod
    def finally_after(self, hook_context: HookContext, hints: dict):
        """
        Run after flag evaluation, including any error processing.
        This will always run. Errors will be swallowed.

        :param hook_context: Information about the particular flag evaluation
        :param hints: A mapping of data for users to communicate to the hooks.
        """
        pass

    @abstractmethod
    def supports_flag_value_type(self, flag_type: FlagType) -> bool:
        """
        Check to see if the hook supports the particular flag type.

        :param flag_type: particular type of the flag
        :return: a boolean containing whether the flag type is supported (True)
        or not (False)
        """
        return True

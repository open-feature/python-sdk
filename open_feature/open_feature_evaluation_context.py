from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.exceptions import GeneralError

_evaluation_context = EvaluationContext()


def api_evaluation_context() -> EvaluationContext:
    global _evaluation_context
    return _evaluation_context


def set_api_evaluation_context(evaluation_context: EvaluationContext):
    global _evaluation_context
    if evaluation_context is None:
        raise GeneralError(error_message="No api level evaluation context")
    _evaluation_context = evaluation_context

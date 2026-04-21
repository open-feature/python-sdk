from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context import (
    ContextVarsTransactionContextPropagator,
    set_transaction_context,
    set_transaction_context_propagator,
)


def before_scenario(context, scenario):
    api.clear_providers()
    api.clear_hooks()
    api.set_evaluation_context(EvaluationContext())
    set_transaction_context_propagator(ContextVarsTransactionContextPropagator())
    set_transaction_context(EvaluationContext())

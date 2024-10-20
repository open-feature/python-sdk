from concurrent.futures import ThreadPoolExecutor

from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context import ContextVarTransactionContextPropagator


def test_contextvar_transaction_context_propagator():
    propagator = ContextVarTransactionContextPropagator()

    context = propagator.get_transaction_context()
    assert isinstance(context, EvaluationContext)

    context = EvaluationContext(targeting_key="foo", attributes={"key": "value"})
    propagator.set_transaction_context(context)
    transaction_context = propagator.get_transaction_context()

    assert transaction_context.targeting_key == "foo"
    assert transaction_context.attributes == {"key": "value"}

    def thread_fn():
        thread_context = propagator.get_transaction_context()
        assert thread_context.targeting_key is None
        assert thread_context.attributes == {}

    with ThreadPoolExecutor() as executor:
        future = executor.submit(thread_fn)

    future.result()

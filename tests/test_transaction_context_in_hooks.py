from openfeature.api import (
    set_provider,
    set_transaction_context,
    set_transaction_context_propagator,
)
from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.hook import Hook
from openfeature.provider.no_op_provider import NoOpProvider
from openfeature.transaction_context import ContextVarsTransactionContextPropagator


class TransactionContextHook(Hook):
    def __init__(self):
        self.before_called = False
        self.transaction_attr_value = None

    def before(self, hook_context, hints):
        self.before_called = True
        # Check if the transaction context attribute is in the hook context
        if "transaction_attr" in hook_context.evaluation_context.attributes:
            self.transaction_attr_value = hook_context.evaluation_context.attributes[
                "transaction_attr"
            ]
        return None


def test_transaction_context_merged_into_hook_context():
    """Test that transaction context is merged into the hook context's evaluation context."""
    set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

    provider = NoOpProvider()
    set_provider(provider)

    client = OpenFeatureClient(domain=None, version=None)

    hook = TransactionContextHook()
    client.add_hooks([hook])

    transaction_context = EvaluationContext(
        targeting_key="transaction",
        attributes={"transaction_attr": "transaction_value"},
    )
    set_transaction_context(transaction_context)

    client.get_boolean_value(flag_key="test-flag", default_value=False)

    assert hook.before_called, "Hook's before method was not called"
    assert hook.transaction_attr_value == "transaction_value", (
        "Transaction context attribute was not found in hook context"
    )

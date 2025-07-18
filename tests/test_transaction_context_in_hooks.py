import pytest
from unittest.mock import MagicMock

from openfeature.api import set_provider, set_transaction_context, set_transaction_context_propagator
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
            self.transaction_attr_value = hook_context.evaluation_context.attributes["transaction_attr"]
        return None


def test_transaction_context_merged_into_hook_context():
    """Test that transaction context is merged into the hook context's evaluation context."""
    # Set up transaction context propagator
    set_transaction_context_propagator(ContextVarsTransactionContextPropagator())
    
    # Set up a provider
    provider = NoOpProvider()
    set_provider(provider)
    
    # Create a client
    client = OpenFeatureClient(domain=None, version=None)
    
    # Create and add a hook that will check for transaction context
    hook = TransactionContextHook()
    client.add_hooks([hook])
    
    # Set transaction context with a specific attribute
    transaction_context = EvaluationContext(
        targeting_key="transaction",
        attributes={"transaction_attr": "transaction_value"},
    )
    set_transaction_context(transaction_context)
    
    # Evaluate a flag
    client.get_boolean_value(flag_key="test-flag", default_value=False)
    
    # Verify that the hook was called and saw the transaction context
    assert hook.before_called, "Hook's before method was not called"
    assert hook.transaction_attr_value == "transaction_value", \
        "Transaction context attribute was not found in hook context"
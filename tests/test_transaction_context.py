import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from openfeature.api import (
    get_transaction_context,
    set_transaction_context,
    set_transaction_context_propagator,
)
from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context import (
    ContextVarsTransactionContextPropagator,
    TransactionContextPropagator,
)
from openfeature.transaction_context.no_op_transaction_context_propagator import (
    NoOpTransactionContextPropagator,
)


# Test cases
def test_should_return_default_evaluation_context_with_noop_propagator():
    # Given
    set_transaction_context_propagator(NoOpTransactionContextPropagator())

    # When
    context = get_transaction_context()

    # Then
    assert isinstance(context, EvaluationContext)
    assert context.attributes == {}


def test_should_set_and_get_custom_transaction_context():
    # Given
    set_transaction_context_propagator(ContextVarsTransactionContextPropagator())
    evaluation_context = EvaluationContext("custom_key", {"attr1": "val1"})

    # When
    set_transaction_context(evaluation_context)

    # Then
    context = get_transaction_context()
    assert context.targeting_key == "custom_key"
    assert context.attributes == {"attr1": "val1"}


def test_should_override_propagator_and_reset_context():
    # Given
    custom_propagator = MagicMock(spec=TransactionContextPropagator)
    default_context = EvaluationContext()

    set_transaction_context_propagator(custom_propagator)

    # When
    set_transaction_context_propagator(NoOpTransactionContextPropagator())

    # Then
    assert get_transaction_context() == default_context


def test_should_call_set_transaction_context_on_propagator():
    # Given
    custom_propagator = MagicMock(spec=TransactionContextPropagator)
    evaluation_context = EvaluationContext("custom_key", {"attr1": "val1"})
    set_transaction_context_propagator(custom_propagator)

    # When
    set_transaction_context(evaluation_context)

    # Then
    custom_propagator.set_transaction_context.assert_called_with(evaluation_context)


def test_should_return_default_context_with_noop_propagator_set():
    # Given
    noop_propagator = NoOpTransactionContextPropagator()

    set_transaction_context_propagator(noop_propagator)

    # When
    context = get_transaction_context()

    # Then
    assert context == EvaluationContext()


def test_should_propagate_event_when_context_set():
    # Given
    custom_propagator = ContextVarsTransactionContextPropagator()
    set_transaction_context_propagator(custom_propagator)
    evaluation_context = EvaluationContext("custom_key", {"attr1": "val1"})

    # When
    set_transaction_context(evaluation_context)

    # Then
    assert (
        custom_propagator._transaction_context_var.get().targeting_key == "custom_key"
    )
    assert custom_propagator._transaction_context_var.get().attributes == {
        "attr1": "val1"
    }


def test_context_vars_transaction_context_propagator_multiple_threads():
    # Given
    context_var_propagator = ContextVarsTransactionContextPropagator()
    set_transaction_context_propagator(context_var_propagator)

    number_of_threads = 3
    barrier = threading.Barrier(number_of_threads)

    def thread_func(context_value, result_list, index):
        context = EvaluationContext(
            f"context_{context_value}", {"thread": context_value}
        )
        set_transaction_context(context)
        barrier.wait()
        result_list[index] = get_transaction_context()

    results = [None] * number_of_threads
    threads = []

    # When
    for i in range(3):
        thread = threading.Thread(target=thread_func, args=(i, results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Then
    for i in range(3):
        assert results[i].targeting_key == f"context_{i}"
        assert results[i].attributes == {"thread": i}


@pytest.mark.asyncio
async def test_context_vars_transaction_context_propagator_asyncio():
    # Given
    context_var_propagator = ContextVarsTransactionContextPropagator()
    set_transaction_context_propagator(context_var_propagator)

    number_of_tasks = 3
    event = asyncio.Event()
    ready_count = 0

    async def async_func(context_value, results, index):
        nonlocal ready_count
        context = EvaluationContext(
            f"context_{context_value}", {"async": context_value}
        )
        set_transaction_context(context)

        ready_count += 1  # Increment the ready count
        if ready_count == number_of_tasks:
            event.set()  # Set the event when all tasks are ready

        await event.wait()  # Wait for the event to be set
        results[index] = get_transaction_context()

    # Placeholder for results
    results = [None] * number_of_tasks

    # When
    tasks = [async_func(i, results, i) for i in range(number_of_tasks)]
    await asyncio.gather(*tasks)

    # Then
    for i in range(number_of_tasks):
        assert results[i].targeting_key == f"context_{i}"
        assert results[i].attributes == {"async": i}

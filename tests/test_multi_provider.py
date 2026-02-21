import pytest

from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import GeneralError
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.provider import Metadata
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider
from openfeature.provider.multi_provider import (
    FirstMatchStrategy,
    MultiProvider,
    ProviderEntry,
)
from openfeature.provider.no_op_provider import NoOpProvider


def test_multi_provider_requires_at_least_one_provider():
    # Given/When/Then
    with pytest.raises(ValueError, match="At least one provider must be provided"):
        MultiProvider([])


def test_multi_provider_uses_explicit_names():
    # Given
    provider_a = NoOpProvider()
    provider_b = NoOpProvider()
    
    # When
    multi = MultiProvider([
        ProviderEntry(provider_a, name="first"),
        ProviderEntry(provider_b, name="second"),
    ])
    
    # Then
    assert len(multi._registered_providers) == 2
    assert multi._registered_providers[0][0] == "first"
    assert multi._registered_providers[1][0] == "second"


def test_multi_provider_generates_unique_names_when_metadata_conflicts():
    # Given
    provider_a = NoOpProvider()
    provider_b = NoOpProvider()
    
    # When - both have same metadata name "NoOpProvider"
    multi = MultiProvider([
        ProviderEntry(provider_a),
        ProviderEntry(provider_b),
    ])
    
    # Then - names are auto-indexed
    assert len(multi._registered_providers) == 2
    names = [name for name, _ in multi._registered_providers]
    assert names == ["NoOpProvider_1", "NoOpProvider_2"]


def test_multi_provider_rejects_duplicate_explicit_names():
    # Given
    provider_a = NoOpProvider()
    provider_b = NoOpProvider()
    
    # When/Then
    with pytest.raises(ValueError, match="Provider name 'duplicate' is not unique"):
        MultiProvider([
            ProviderEntry(provider_a, name="duplicate"),
            ProviderEntry(provider_b, name="duplicate"),
        ])


def test_multi_provider_first_match_strategy_sequential():
    # Given
    flags_a = {
        "flag1": InMemoryFlag("off", {"on": True, "off": False}),
    }
    flags_b = {
        "flag1": InMemoryFlag("on", {"on": True, "off": False}),
        "flag2": InMemoryFlag("on", {"on": True, "off": False}),
    }
    
    provider_a = InMemoryProvider(flags_a)
    provider_b = InMemoryProvider(flags_b)
    
    multi = MultiProvider([
        ProviderEntry(provider_a, name="primary"),
        ProviderEntry(provider_b, name="fallback"),
    ], strategy=FirstMatchStrategy())
    
    # When - flag1 exists in both, should use first (primary)
    result = multi.resolve_boolean_details("flag1", False)
    
    # Then
    assert result.value == False  # primary provider returns "off" variant
    assert result.reason != Reason.ERROR


def test_multi_provider_fallback_to_second_provider():
    # Given
    flags_a = {}  # primary has no flags
    flags_b = {
        "flag1": InMemoryFlag("on", {"on": True, "off": False}),
    }
    
    provider_a = InMemoryProvider(flags_a)
    provider_b = InMemoryProvider(flags_b)
    
    multi = MultiProvider([
        ProviderEntry(provider_a, name="primary"),
        ProviderEntry(provider_b, name="fallback"),
    ])
    
    # When - flag1 doesn't exist in primary, should fallback
    result = multi.resolve_boolean_details("flag1", False)
    
    # Then
    assert result.value == True  # fallback provider has the flag
    assert result.reason != Reason.ERROR


def test_multi_provider_all_types_work():
    # Given
    flags = {
        "bool-flag": InMemoryFlag("on", {"on": True, "off": False}),
        "string-flag": InMemoryFlag("greeting", {"greeting": "hello", "farewell": "goodbye"}),
        "int-flag": InMemoryFlag("big", {"small": 10, "big": 100}),
        "float-flag": InMemoryFlag("pi", {"pi": 3.14, "e": 2.71}),
        "object-flag": InMemoryFlag("full", {
            "full": {"name": "test", "value": 42},
            "empty": {},
        }),
    }
    
    provider = InMemoryProvider(flags)
    multi = MultiProvider([ProviderEntry(provider)])
    
    # When/Then
    bool_result = multi.resolve_boolean_details("bool-flag", False)
    assert bool_result.value == True
    
    string_result = multi.resolve_string_details("string-flag", "default")
    assert string_result.value == "hello"
    
    int_result = multi.resolve_integer_details("int-flag", 0)
    assert int_result.value == 100
    
    float_result = multi.resolve_float_details("float-flag", 0.0)
    assert float_result.value == 3.14
    
    object_result = multi.resolve_object_details("object-flag", {})
    assert object_result.value == {"name": "test", "value": 42}


def test_multi_provider_initialize_all_providers():
    # Given
    provider_a = NoOpProvider()
    provider_b = NoOpProvider()
    
    # Track if initialize was called
    provider_a.initialize = lambda ctx: None
    provider_b.initialize = lambda ctx: None
    
    a_initialized = False
    b_initialized = False
    
    def track_a_init(ctx):
        nonlocal a_initialized
        a_initialized = True
    
    def track_b_init(ctx):
        nonlocal b_initialized
        b_initialized = True
    
    provider_a.initialize = track_a_init
    provider_b.initialize = track_b_init
    
    multi = MultiProvider([
        ProviderEntry(provider_a),
        ProviderEntry(provider_b),
    ])
    
    # When
    multi.initialize(EvaluationContext())
    
    # Then
    assert a_initialized
    assert b_initialized


def test_multi_provider_initialization_failures_are_aggregated():
    # Given
    provider_a = NoOpProvider()
    provider_b = NoOpProvider()
    
    def fail_init(ctx):
        raise Exception("Init failed")
    
    provider_a.initialize = fail_init
    provider_b.initialize = fail_init
    
    multi = MultiProvider([
        ProviderEntry(provider_a, name="a"),
        ProviderEntry(provider_b, name="b"),
    ])
    
    # When/Then
    with pytest.raises(GeneralError, match="Multi-provider initialization failed"):
        multi.initialize(EvaluationContext())


def test_multi_provider_returns_error_when_no_providers_have_flag():
    # Given
    provider_a = InMemoryProvider({})
    provider_b = InMemoryProvider({})
    
    multi = MultiProvider([
        ProviderEntry(provider_a),
        ProviderEntry(provider_b),
    ])
    
    # When
    result = multi.resolve_boolean_details("nonexistent", False)
    
    # Then
    assert result.value == False  # default value
    assert result.reason == Reason.ERROR


@pytest.mark.asyncio
async def test_multi_provider_async_methods_work():
    # Given
    flags = {
        "async-flag": InMemoryFlag("on", {"on": True, "off": False}),
    }
    provider = InMemoryProvider(flags)
    multi = MultiProvider([ProviderEntry(provider)])
    
    # When
    result = await multi.resolve_boolean_details_async("async-flag", False)
    
    # Then
    assert result.value == True
    assert result.reason != Reason.ERROR


def test_multi_provider_can_be_used_with_api():
    # Given
    api.clear_providers()
    flags = {
        "api-flag": InMemoryFlag("on", {"on": True, "off": False}),
    }
    provider = InMemoryProvider(flags)
    multi = MultiProvider([ProviderEntry(provider)])
    
    # When
    api.set_provider(multi)
    client = api.get_client()
    value = client.get_boolean_value("api-flag", False)
    
    # Then
    assert value == True


def test_multi_provider_metadata():
    # Given
    multi = MultiProvider([ProviderEntry(NoOpProvider())])
    
    # When
    metadata = multi.get_metadata()
    
    # Then
    assert metadata.name == "MultiProvider"


def test_multi_provider_aggregates_hooks():
    # Given
    from unittest.mock import MagicMock
    
    provider_a = NoOpProvider()
    provider_b = NoOpProvider()
    
    hook_a = MagicMock()
    hook_b = MagicMock()
    
    provider_a.get_provider_hooks = lambda: [hook_a]
    provider_b.get_provider_hooks = lambda: [hook_b]
    
    multi = MultiProvider([
        ProviderEntry(provider_a),
        ProviderEntry(provider_b),
    ])
    
    # When
    hooks = multi.get_provider_hooks()
    
    # Then
    assert len(hooks) == 2
    assert hook_a in hooks
    assert hook_b in hooks

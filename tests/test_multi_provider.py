import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.event import ProviderEvent, ProviderEventDetails
from openfeature.exception import ErrorCode, GeneralError
from openfeature.flag_evaluation import (
    FlagEvaluationDetails,
    FlagResolutionDetails,
    Reason,
)
from openfeature.hook import Hook, HookContext, HookHints
from openfeature.provider import (
    AbstractProvider,
    ComparisonStrategy,
    FirstMatchStrategy,
    FirstSuccessfulStrategy,
    Metadata,
    MultiProvider,
    ProviderEntry,
    ProviderStatus,
)


class BooleanProvider(AbstractProvider):
    def __init__(
        self,
        name: str,
        boolean_result: FlagResolutionDetails[bool] | None = None,
        boolean_exception: Exception | None = None,
        hook_list: list[Hook] | None = None,
        sync_blocker: "SyncBlocker | None" = None,
        async_blocker: "AsyncBlocker | None" = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.booleanResult = boolean_result
        self.booleanException = boolean_exception
        self.hookList = hook_list or []
        self.sync_blocker = sync_blocker
        self.async_blocker = async_blocker
        self.resolveCount = 0
        self.seenContexts: list[dict[str, object]] = []

    def get_metadata(self) -> Metadata:
        return Metadata(name=self.name)

    def get_provider_hooks(self) -> list[Hook]:
        return self.hookList

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        del flag_key
        self.resolveCount += 1
        self.seenContexts.append(dict((evaluation_context or EvaluationContext()).attributes))
        if self.sync_blocker is not None:
            self.sync_blocker.wait()
        if self.booleanException is not None:
            raise self.booleanException
        if self.booleanResult is not None:
            return self.booleanResult
        return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[bool]:
        del flag_key
        self.resolveCount += 1
        self.seenContexts.append(dict((evaluation_context or EvaluationContext()).attributes))
        if self.async_blocker is not None:
            await self.async_blocker.wait()
        if self.booleanException is not None:
            raise self.booleanException
        if self.booleanResult is not None:
            return self.booleanResult
        return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[str]:
        del flag_key
        del evaluation_context
        return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[int]:
        del flag_key
        del evaluation_context
        return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[float]:
        del flag_key
        del evaluation_context
        return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: dict | list,
        evaluation_context: EvaluationContext | None = None,
    ) -> FlagResolutionDetails[dict | list]:
        del flag_key
        del evaluation_context
        return FlagResolutionDetails(value=default_value, reason=Reason.DEFAULT)


class RecordingHook(Hook):
    def __init__(self, hook_name: str) -> None:
        self.hookName = hook_name
        self.events: list[str] = []

    def before(
        self, hook_context: HookContext, hints: HookHints
    ) -> EvaluationContext | None:
        del hook_context
        del hints
        self.events.append("before")
        return EvaluationContext(attributes={"hookOwner": self.hookName})

    def after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[object],
        hints: HookHints,
    ) -> None:
        del hook_context
        del details
        del hints
        self.events.append("after")

    def error(
        self, hook_context: HookContext, exception: Exception, hints: HookHints
    ) -> None:
        del hook_context
        del exception
        del hints
        self.events.append("error")

    def finally_after(
        self,
        hook_context: HookContext,
        details: FlagEvaluationDetails[object],
        hints: HookHints,
    ) -> None:
        del hook_context
        del details
        del hints
        self.events.append("finally")


class SyncBlocker:
    def __init__(self, expected_count: int) -> None:
        self.expectedCount = expected_count
        self.enteredCount = 0
        self.enteredEvent = threading.Event()
        self.releaseEvent = threading.Event()
        self.lock = threading.Lock()

    def wait(self) -> None:
        with self.lock:
            self.enteredCount += 1
            if self.enteredCount == self.expectedCount:
                self.enteredEvent.set()
        assert self.releaseEvent.wait(timeout=2)


class AsyncBlocker:
    def __init__(self, expected_count: int) -> None:
        self.expectedCount = expected_count
        self.enteredCount = 0
        self.enteredEvent = asyncio.Event()
        self.releaseEvent = asyncio.Event()
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self.lock:
            self.enteredCount += 1
            if self.enteredCount == self.expectedCount:
                self.enteredEvent.set()
        await asyncio.wait_for(self.releaseEvent.wait(), timeout=2)


def test_multi_provider_requires_at_least_one_provider():
    with pytest.raises(ValueError, match="At least one provider must be provided"):
        MultiProvider([])


def test_multi_provider_rejects_duplicate_explicit_names():
    first_provider = BooleanProvider("provider")
    second_provider = BooleanProvider("provider")

    with pytest.raises(ValueError, match="Provider name 'duplicate' is not unique"):
        MultiProvider(
            [
                ProviderEntry(first_provider, name="duplicate"),
                ProviderEntry(second_provider, name="duplicate"),
            ]
        )


def test_comparison_strategy_rejects_unknown_fallback_provider():
    first_provider = BooleanProvider("first")
    second_provider = BooleanProvider("second")

    with pytest.raises(ValueError, match="Fallback provider 'missing' is not registered"):
        MultiProvider(
            [
                ProviderEntry(first_provider, name="first"),
                ProviderEntry(second_provider, name="second"),
            ],
            strategy=ComparisonStrategy(fallback_provider="missing"),
        )


def test_first_match_uses_fallback_after_flag_not_found():
    missing_result = FlagResolutionDetails(
        value=False,
        reason=Reason.ERROR,
        error_code=ErrorCode.FLAG_NOT_FOUND,
        error_message="missing",
    )
    first_provider = BooleanProvider("first", boolean_result=missing_result)
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstMatchStrategy(),
    )

    result = multi_provider.resolve_boolean_details("flagKey", False)

    assert result.value is True
    assert first_provider.resolveCount == 1
    assert second_provider.resolveCount == 1


def test_first_match_stops_on_non_flag_not_found_error():
    error_result = FlagResolutionDetails(
        value=False,
        reason=Reason.ERROR,
        error_code=ErrorCode.GENERAL,
        error_message="boom",
    )
    first_provider = BooleanProvider("first", boolean_result=error_result)
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstMatchStrategy(),
    )

    result = multi_provider.resolve_boolean_details("flagKey", False)

    assert result.error_code == ErrorCode.GENERAL
    assert second_provider.resolveCount == 0


def test_first_successful_skips_general_errors():
    first_provider = BooleanProvider("first", boolean_exception=GeneralError("broken"))
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstSuccessfulStrategy(),
    )

    result = multi_provider.resolve_boolean_details("flagKey", False)

    assert result.value is True
    assert first_provider.resolveCount == 1
    assert second_provider.resolveCount == 1


def test_first_successful_aggregates_errors_when_all_providers_fail():
    first_provider = BooleanProvider("first", boolean_exception=GeneralError("first"))
    second_provider = BooleanProvider("second", boolean_exception=GeneralError("second"))
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstSuccessfulStrategy(),
    )

    result = multi_provider.resolve_boolean_details("flagKey", False)

    assert result.error_code == ErrorCode.GENERAL
    assert "first: GENERAL (first)" in result.error_message
    assert "second: GENERAL (second)" in result.error_message


def test_comparison_strategy_returns_fallback_value_and_calls_on_mismatch():
    mismatch_spy = MagicMock()
    first_provider = BooleanProvider(
        "first",
        boolean_result=FlagResolutionDetails(value=False, reason=Reason.STATIC),
    )
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=ComparisonStrategy(
            fallback_provider="second",
            on_mismatch=mismatch_spy,
        ),
    )

    result = multi_provider.resolve_boolean_details("flagKey", False)

    assert result.value is True
    mismatch_spy.assert_called_once()


def test_comparison_strategy_aggregates_provider_errors():
    first_provider = BooleanProvider("first", boolean_exception=GeneralError("first"))
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=ComparisonStrategy(),
    )

    result = multi_provider.resolve_boolean_details("flagKey", False)

    assert result.error_code == ErrorCode.GENERAL
    assert "first: GENERAL (first)" in result.error_message


def test_multi_provider_runs_sync_parallel_evaluation():
    sync_blocker = SyncBlocker(expected_count=2)
    first_provider = BooleanProvider(
        "first",
        boolean_result=FlagResolutionDetails(value=False, reason=Reason.STATIC),
        sync_blocker=sync_blocker,
    )
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
        sync_blocker=sync_blocker,
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstSuccessfulStrategy(run_mode="parallel"),
    )

    result_holder: list[FlagResolutionDetails[bool]] = []

    def evaluate() -> None:
        result_holder.append(multi_provider.resolve_boolean_details("flagKey", False))

    worker_thread = threading.Thread(target=evaluate)
    worker_thread.start()

    assert sync_blocker.enteredEvent.wait(timeout=2)
    sync_blocker.releaseEvent.set()
    worker_thread.join(timeout=2)

    assert result_holder[0].value is False
    assert first_provider.resolveCount == 1
    assert second_provider.resolveCount == 1


@pytest.mark.asyncio
async def test_multi_provider_runs_async_parallel_evaluation():
    async_blocker = AsyncBlocker(expected_count=2)
    first_provider = BooleanProvider(
        "first",
        boolean_result=FlagResolutionDetails(value=False, reason=Reason.STATIC),
        async_blocker=async_blocker,
    )
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
        async_blocker=async_blocker,
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstSuccessfulStrategy(run_mode="parallel"),
    )

    evaluation_task = asyncio.create_task(
        multi_provider.resolve_boolean_details_async("flagKey", False)
    )

    await asyncio.wait_for(async_blocker.enteredEvent.wait(), timeout=2)
    async_blocker.releaseEvent.set()
    result = await asyncio.wait_for(evaluation_task, timeout=2)

    assert result.value is False
    assert first_provider.resolveCount == 1
    assert second_provider.resolveCount == 1


def test_multi_provider_isolates_provider_hooks_and_runs_lifecycle():
    first_hook = RecordingHook("first")
    second_hook = RecordingHook("second")
    first_provider = BooleanProvider(
        "first",
        boolean_result=FlagResolutionDetails(
            value=False,
            reason=Reason.ERROR,
            error_code=ErrorCode.FLAG_NOT_FOUND,
            error_message="missing",
        ),
        hook_list=[first_hook],
    )
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
        hook_list=[second_hook],
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstMatchStrategy(),
    )

    api.set_provider(multi_provider)
    client = api.get_client()
    result = client.get_boolean_details(
        "flagKey",
        False,
        evaluation_context=EvaluationContext(attributes={"base": "value"}),
    )

    assert result.value is True
    assert first_hook.events == ["before", "error", "finally"]
    assert second_hook.events == ["before", "after", "finally"]
    assert first_provider.seenContexts[0]["base"] == "value"
    assert first_provider.seenContexts[0]["hookOwner"] == "first"
    assert second_provider.seenContexts[0]["base"] == "value"
    assert second_provider.seenContexts[0]["hookOwner"] == "second"


def test_multi_provider_does_not_run_unused_provider_hooks():
    first_hook = RecordingHook("first")
    second_hook = RecordingHook("second")
    first_provider = BooleanProvider(
        "first",
        boolean_result=FlagResolutionDetails(value=True, reason=Reason.STATIC),
        hook_list=[first_hook],
    )
    second_provider = BooleanProvider(
        "second",
        boolean_result=FlagResolutionDetails(value=False, reason=Reason.STATIC),
        hook_list=[second_hook],
    )
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ],
        strategy=FirstMatchStrategy(),
    )

    api.set_provider(multi_provider)
    client = api.get_client()
    result = client.get_boolean_details("flagKey", False)

    assert result.value is True
    assert first_hook.events == ["before", "after", "finally"]
    assert second_hook.events == []


def test_multi_provider_aggregates_status_and_deduplicates_events():
    first_provider = BooleanProvider("first")
    second_provider = BooleanProvider("second")
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ]
    )

    api.set_provider(multi_provider)
    client = api.get_client()
    spy = MagicMock()
    client.add_handler(ProviderEvent.PROVIDER_READY, spy.provider_ready)
    client.add_handler(ProviderEvent.PROVIDER_ERROR, spy.provider_error)
    client.add_handler(ProviderEvent.PROVIDER_STALE, spy.provider_stale)
    spy.provider_ready.reset_mock()

    first_provider.emit_provider_stale(ProviderEventDetails(message="stale"))
    assert client.get_provider_status() == ProviderStatus.STALE
    assert spy.provider_stale.call_count == 1

    second_provider.emit_provider_stale(ProviderEventDetails(message="still stale"))
    assert client.get_provider_status() == ProviderStatus.STALE
    assert spy.provider_stale.call_count == 1

    first_provider.emit_provider_error(
        ProviderEventDetails(error_code=ErrorCode.GENERAL, message="error")
    )
    assert client.get_provider_status() == ProviderStatus.ERROR
    assert spy.provider_error.call_count == 1

    second_provider.emit_provider_error(
        ProviderEventDetails(error_code=ErrorCode.PROVIDER_FATAL, message="fatal")
    )
    assert client.get_provider_status() == ProviderStatus.FATAL
    assert spy.provider_error.call_count == 2

    second_provider.emit_provider_ready(ProviderEventDetails())
    assert client.get_provider_status() == ProviderStatus.ERROR
    assert spy.provider_error.call_count == 3

    first_provider.emit_provider_ready(ProviderEventDetails())
    assert client.get_provider_status() == ProviderStatus.READY
    assert spy.provider_ready.call_count == 1


def test_multi_provider_forwards_configuration_changed_events():
    first_provider = BooleanProvider("first")
    second_provider = BooleanProvider("second")
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ]
    )

    api.set_provider(multi_provider)
    client = api.get_client()
    spy = MagicMock()
    client.add_handler(
        ProviderEvent.PROVIDER_CONFIGURATION_CHANGED,
        spy.provider_configuration_changed,
    )

    first_provider.emit_provider_configuration_changed(ProviderEventDetails(message="one"))
    second_provider.emit_provider_configuration_changed(ProviderEventDetails(message="two"))

    assert spy.provider_configuration_changed.call_count == 2


def test_multi_provider_reports_not_ready_after_shutdown():
    first_provider = BooleanProvider("first")
    second_provider = BooleanProvider("second")
    multi_provider = MultiProvider(
        [
            ProviderEntry(first_provider, name="first"),
            ProviderEntry(second_provider, name="second"),
        ]
    )

    api.set_provider(multi_provider)
    client = api.get_client()

    api.shutdown()

    assert client.get_provider_status() == ProviderStatus.NOT_READY

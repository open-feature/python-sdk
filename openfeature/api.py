import typing

from openfeature.client import OpenFeatureClient
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import GeneralError
from openfeature.hook import Hook
from openfeature.provider import FeatureProvider
from openfeature.provider.metadata import Metadata
from openfeature.provider.no_op_provider import NoOpProvider

_provider: FeatureProvider = NoOpProvider()

_evaluation_context = EvaluationContext()

_hooks: typing.List[Hook] = []


def get_client(
    name: typing.Optional[str] = None, version: typing.Optional[str] = None
) -> OpenFeatureClient:
    return OpenFeatureClient(name=name, version=version, provider=_provider)


def set_provider(provider: FeatureProvider) -> None:
    global _provider
    if provider is None:
        raise GeneralError(error_message="No provider")
    if _provider:
        _provider.shutdown()
    _provider = provider
    provider.initialize(_evaluation_context)


def get_provider() -> FeatureProvider:
    global _provider
    return _provider


def get_provider_metadata() -> Metadata:
    global _provider
    return _provider.get_metadata()


def get_evaluation_context() -> EvaluationContext:
    global _evaluation_context
    return _evaluation_context


def set_evaluation_context(evaluation_context: EvaluationContext) -> None:
    global _evaluation_context
    if evaluation_context is None:
        raise GeneralError(error_message="No api level evaluation context")
    _evaluation_context = evaluation_context


def add_hooks(hooks: typing.List[Hook]) -> None:
    global _hooks
    _hooks = _hooks + hooks


def clear_hooks() -> None:
    global _hooks
    _hooks = []


def get_hooks() -> typing.List[Hook]:
    global _hooks
    return _hooks


def shutdown() -> None:
    _provider.shutdown()

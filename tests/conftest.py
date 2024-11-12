import pytest

from openfeature import api
from openfeature.provider.no_op_provider import AsyncNoOpProvider, NoOpProvider


@pytest.fixture(autouse=True)
def clear_providers():
    """
    For tests that use set_provider(), we need to clear the provider to avoid issues
    in other tests.
    """
    api.clear_providers()


@pytest.fixture(autouse=True)
def clear_hooks_fixture():
    """
    For tests that use add_hooks(), we need to clear the hooks to avoid issues
    in other tests.
    """
    api.clear_hooks()


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()


@pytest.fixture()
def no_op_provider_client_async():
    api.set_provider(AsyncNoOpProvider())
    return api.get_client_async("my-async-client")

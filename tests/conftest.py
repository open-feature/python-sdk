import pytest

from openfeature import api
from openfeature.provider.no_op_provider import NoOpProvider


@pytest.fixture(autouse=True)
def clear_provider():
    """
    For tests that use set_provider(), we need to clear the provider to avoid issues
    in other tests.
    """
    yield
    _provider = None


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()

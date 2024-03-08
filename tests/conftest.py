import pytest

from openfeature import api
from openfeature.provider.no_op_provider import NoOpProvider


@pytest.fixture(autouse=True)
def clear_providers():
    """
    For tests that use set_provider(), we need to clear the provider to avoid issues
    in other tests.
    """
    api.clear_providers()


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()

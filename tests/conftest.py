import pytest

from openfeature import api
from openfeature.provider.no_op_provider import NoOpProvider


@pytest.fixture(autouse=True)
def clear_providers():
    """Fully reset the global default API between tests to avoid cross-test pollution."""
    api.shutdown()


@pytest.fixture()
def no_op_provider_client():
    api.set_provider_and_wait(NoOpProvider())
    return api.get_client()

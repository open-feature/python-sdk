import pytest

from open_feature import open_feature_api as api
from open_feature.provider.no_op_provider import NoOpProvider


@pytest.fixture(autouse=True)
def clear_provider():
    """
    For tests that use set_provider(), we need to clear the provider to avoid issues
    in other tests.
    """
    yield
    _provider = None  # noqa: F841


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()

import pytest

from open_feature import open_feature_api as api
from open_feature.provider.no_op_provider import NoOpProvider


@pytest.fixture(autouse=True)
def clear_provider():
    yield
    # Setting private provider back to None to ensure other tests aren't affected
    _provider = None  # noqa: F841


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()

import pytest

from python_open_feature_sdk import open_feature_api as api
from python_open_feature_sdk.provider.no_op_provider import NoOpProvider


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()

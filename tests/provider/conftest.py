import pytest

from open_feature import open_feature_api as api
from open_feature.provider.no_op_provider import NoOpProvider
from open_feature.provider.flagd_provider import FlagDProvider


@pytest.fixture()
def no_op_provider_client():
    api.set_provider(NoOpProvider())
    return api.get_client()

@pytest.fixture()
def flagd_provider_client():
    api.set_provider(FlagDProvider())
    return api.get_client()

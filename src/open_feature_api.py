from src.open_feature_client import OpenFeatureClient
from src.provider.provider import AbstractProvider

global provider


class OpenFeatureAPI:
    def __init__(self):
        pass

    @staticmethod
    def get_client(
        name: str = None, version: str = None, provider=None
    ) -> OpenFeatureClient:
        if provider is None:
            open_feature_provider = OpenFeatureAPI.get_provider()
        else:
            OpenFeatureAPI.set_provider(provider)
            open_feature_provider = provider

        return OpenFeatureClient(
            name=name, version=version, provider=open_feature_provider
        )

    @staticmethod
    def set_provider(provider_type: AbstractProvider):
        if provider_type is None:
            raise TypeError("No provider")
        global provider
        provider = provider_type

    @staticmethod
    def get_provider() -> AbstractProvider:
        global provider
        return provider

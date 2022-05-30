from src.provider.provider import AbstractProvider

global provider


class OpenFeature:
    def __init__(self):
        pass

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

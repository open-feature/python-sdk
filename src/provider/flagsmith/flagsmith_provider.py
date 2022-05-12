from numbers import Number

import flagsmith as Flagsmith

from src.provider.provider import AbstractProvider


class FlagsmithProvider(AbstractProvider):
    def __init__(self, flagsmith: Flagsmith = None):
        if flagsmith is None:
            self.flagsmith_provider = Flagsmith(environment_id="<YOUR_ENVIRONMENT_KEY>")
        else:
            self.flagsmith_provider = flagsmith

    def get_boolean_value(self, key: str, defaultValue: bool) -> bool:
        value = self.flagsmith_provider.get_value(key)

    def get_boolean_details(self, key: str, defaultValue: bool):
        pass

    def get_string_value(self, key: str, defaultValue: bool) -> str:
        value = self.flagsmith_provider.get_value(key)

    def get_string_details(self, key: str, defaultValue: bool):
        pass

    def get_number_value(self, key: str, defaultValue: bool) -> Number:
        value = self.flagsmith_provider.get_value(key)

    def get_number_details(self, key: str, defaultValue: bool):
        pass

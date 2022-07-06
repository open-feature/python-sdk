from open_feature.flag_evaluation.flag_type import FlagType


class HookContext:
    def __init__(  # noqa: CFQ002
        self,
        flag_key: str,
        flag_type: FlagType,
        default_value,
        ctx,
        client_metadata=None,
        provider_metadata=None,
    ):
        self.flag_key = flag_key
        self.flag_type = flag_type
        self.default_value = default_value
        self.ctx = ctx
        self.client_metadata = client_metadata
        self.provider_metadata = provider_metadata

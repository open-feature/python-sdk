import typing
from src.flag.abstact_flag import AbstractFlag


class StringFlag(AbstractFlag):
    def __init__(
        self,
        key: str,
        default_value: str,
        evaluation_context: typing.Any,
        flag_evaluation_context: typing.Any,
    ) -> None:
        self.default_value = default_value
        super().__init__(key, evaluation_context, flag_evaluation_context)

    @property
    def value(self) -> str:
        pass

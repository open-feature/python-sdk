import typing


class AbstractFlag:
    def __init__(
        self,
        key: str,
        evaluation_context: typing.Any,
        flag_evaluation_context typing.Any,
    ) -> None:
        self.key = key
        self.evaluation_context = evaluation_context
        self.flag_evaluation_context = flag_evaluation_context

    @property
    def value(self):
        raise NotImplementedError()

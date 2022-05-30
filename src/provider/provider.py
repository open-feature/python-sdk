import typing
from abc import abstractmethod
from numbers import Number


class AbstractProvider:
    @abstractmethod
    def get_boolean_value(
        self,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ) -> bool:
        pass

    @abstractmethod
    def get_boolean_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        pass

    @abstractmethod
    def get_string_value(
        self,
        key: str,
        default_value: str,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ) -> str:
        pass

    @abstractmethod
    def get_string_details(
        self,
        key: str,
        default_value: str,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        pass

    @abstractmethod
    def get_number_value(
        self,
        key: str,
        default_value: Number,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ) -> Number:
        pass

    @abstractmethod
    def get_number_details(
        self,
        key: str,
        default_value: Number,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        pass

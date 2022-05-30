import typing
from numbers import Number

from open_feature import OpenFeature
from src.flag_type import FlagType


class OpenFeatureClient:
    def __init__(self, name: str, version: str, context, hooks: list = []):
        self.name = name
        self.version = version
        self.context = context
        self.hooks = hooks
        self.provider = OpenFeature.get_provider()

    def get_boolean_value(
        self,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ) -> bool:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_boolean_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        return self.provider.get_boolean_details(
            key, default_value, evaluation_context, flag_evaluation_options
        )

    def get_string_value(
        self,
        key: str,
        default_value: str,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ) -> str:
        return self.evaluate_flag(
            FlagType.STRING,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_string_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        return self.provider.get_string_details(
            key, default_value, evaluation_context, flag_evaluation_options
        )

    def get_number_value(
        self,
        key: str,
        default_value: Number,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ) -> Number:
        return self.evaluate_flag(
            FlagType.NUMBER,
            key,
            default_value,
            evaluation_context,
            flag_evaluation_options,
        )

    def get_number_details(
        self,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        return self.provider.get_number_details(
            key, default_value, evaluation_context, flag_evaluation_options
        )

    def evaluate_flag(
        self,
        flag_type: FlagType,
        key: str,
        default_value: bool,
        evaluation_context: typing.Any = None,
        flag_evaluation_options: typing.Any = None,
    ):
        if flag_type is FlagType.BOOLEAN:
            return self.provider.get_boolean_value(
                key, default_value, evaluation_context, flag_evaluation_options
            )
        if flag_type is FlagType.NUMBER:
            return self.provider.get_number_value(
                key, default_value, evaluation_context, flag_evaluation_options
            )
        if flag_type is FlagType.STRING:
            return self.provider.get_string_value(
                key, default_value, evaluation_context, flag_evaluation_options
            )

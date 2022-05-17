from numbers import Number

from open_feature import OpenFeature
from src.flag_type import FlagType


class OpenFeatureClient:
    def __init__(self, name: str, version: str, context, hooks: list = []):
        self.name = name
        self.version = version
        self.context = context
        self.hooks = hooks

    def get_boolean_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> bool:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            defaultValue,
            evaluationContext,
            flagEvaluationOptions,
        )

    def get_boolean_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        return self.get_boolean_details(
            key, defaultValue, evaluationContext, flagEvaluationOptions
        )

    def get_string_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> str:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            defaultValue,
            evaluationContext,
            flagEvaluationOptions,
        )

    def get_string_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        return self.get_string_details(
            key, defaultValue, evaluationContext, flagEvaluationOptions
        )

    def get_number_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> Number:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            defaultValue,
            evaluationContext,
            flagEvaluationOptions,
        )

    def get_number_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        return self.get_number_details(
            key, defaultValue, evaluationContext, flagEvaluationOptions
        )

    def evaluate_flag(
        self,
        flag_type: FlagType,
        key: str,
        defaultValue: bool,
        evaluationContext,
        flagEvaluationOptions,
    ):
        provider = OpenFeature.get_provider()
        if flag_type is FlagType.BOOLEAN:
            return provider.getBooleanEvaluation(
                key, defaultValue, evaluationContext, flagEvaluationOptions
            )
        if flag_type is FlagType.NUMBER:
            return provider.getNumberEvaluation(
                key, defaultValue, evaluationContext, flagEvaluationOptions
            )
        if flag_type is FlagType.STRING:
            return provider.getStringEvaluation(
                key, defaultValue, evaluationContext, flagEvaluationOptions
            )

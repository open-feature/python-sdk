from abc import abstractmethod
from numbers import Number


class AbstractProvider:
    @abstractmethod
    def get_boolean_value(self, key: str, defaultValue: bool) -> bool:
        pass

    @abstractmethod
    def get_boolean_value(
        self, key: str, defaultValue: bool, evaluationContext
    ) -> bool:
        pass

    @abstractmethod
    def get_boolean_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> bool:
        pass

    @abstractmethod
    def get_boolean_details(self, key: str, defaultValue: bool):
        pass

    @abstractmethod
    def get_boolean_details(self, key: str, defaultValue: bool, evaluationContext):
        pass

    @abstractmethod
    def get_boolean_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        pass

    @abstractmethod
    def get_string_value(self, key: str, defaultValue: bool) -> str:
        pass

    @abstractmethod
    def get_string_value(self, key: str, defaultValue: bool, evaluationContext) -> str:
        pass

    @abstractmethod
    def get_string_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> str:
        pass

    @abstractmethod
    def get_string_details(self, key: str, defaultValue: bool):
        pass

    @abstractmethod
    def get_string_details(self, key: str, defaultValue: bool, evaluationContext):
        pass

    @abstractmethod
    def get_string_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        pass

    @abstractmethod
    def get_number_value(self, key: str, defaultValue: bool) -> Number:
        pass

    @abstractmethod
    def get_number_value(
        self, key: str, defaultValue: bool, evaluationContext
    ) -> Number:
        pass

    @abstractmethod
    def get_number_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> Number:
        pass

    @abstractmethod
    def get_number_details(self, key: str, defaultValue: bool):
        pass

    @abstractmethod
    def get_number_details(self, key: str, defaultValue: bool, evaluationContext):
        pass

    @abstractmethod
    def get_number_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        pass

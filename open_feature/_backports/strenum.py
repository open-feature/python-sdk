try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        """
        Backport StrEnum for Python <3.11
        """

        pass

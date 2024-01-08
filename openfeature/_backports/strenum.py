import sys

if sys.version_info >= (3, 11):
    # re-export needed for type checking
    from enum import StrEnum as StrEnum  # noqa: PLC0414
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """
        Backport StrEnum for Python <3.11
        """

        pass

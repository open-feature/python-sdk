from src.exception.exceptions import GeneralError
from src.flag.boolean_flag import BooleanFlag
from src.flag.number_flag import NumberFlag
from src.flag.object_flag import ObjectFlag
from src.flag.string_flag import StringFlag
from src.flag_evaluation.flag_type import FlagType


def flag_factory(flag_type: FlagType):
    if flag_type is FlagType.BOOLEAN:
        return BooleanFlag

    elif flag_type is FlagType.NUMBER:
        return NumberFlag

    elif flag_type is FlagType.OBJECT:
        return ObjectFlag
    # Fallback case is a string object
    elif flag_type is FlagType.STRING:
        return StringFlag
    else:
        raise GeneralError(error_message="Unknown flag type")

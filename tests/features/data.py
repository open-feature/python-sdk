from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.flag_evaluation.reason import Reason
from open_feature.flag_evaluation.resolution_details import FlagResolutionDetails
from open_feature.provider.in_memory_provider import InMemoryFlag


def context_func(flag: InMemoryFlag, evaluation_context: EvaluationContext):
    expects = {"fn": "Sulisław", "ln": "Świętopełk", "age": 29, "customer": False}

    if expects != evaluation_context.attributes:
        return FlagResolutionDetails(
            value=flag.variants[flag.default_variant],
            reason=Reason.DEFAULT,
            variant=flag.default_variant,
        )

    return FlagResolutionDetails(
        value=flag.variants["internal"],
        reason=Reason.TARGETING_MATCH,
        variant="internal",
    )


IN_MEMORY_FLAGS = {
    "boolean-flag": InMemoryFlag(
        flag_key="boolean-flag",
        state=InMemoryFlag.State.ENABLED,
        default_variant="on",
        variants={"on": True, "off": False},
        context_evaluator=None,
    ),
    "string-flag": InMemoryFlag(
        flag_key="string-flag",
        state=InMemoryFlag.State.ENABLED,
        default_variant="greeting",
        variants={"greeting": "hi", "parting": "bye"},
        context_evaluator=None,
    ),
    "integer-flag": InMemoryFlag(
        flag_key="integer-flag",
        state=InMemoryFlag.State.ENABLED,
        default_variant="ten",
        variants={"one": 1, "ten": 10},
        context_evaluator=None,
    ),
    "float-flag": InMemoryFlag(
        flag_key="float-flag",
        state=InMemoryFlag.State.ENABLED,
        default_variant="half",
        variants={"tenth": 0.1, "half": 0.5},
        context_evaluator=None,
    ),
    "object-flag": InMemoryFlag(
        flag_key="object-flag",
        state=InMemoryFlag.State.ENABLED,
        default_variant="template",
        variants={
            "empty": {},
            "template": {
                "showImages": True,
                "title": "Check out these pics!",
                "imagesPerPage": 100,
            },
        },
        context_evaluator=None,
    ),
    "context-aware": InMemoryFlag(
        flag_key="context-aware",
        state=InMemoryFlag.State.ENABLED,
        variants={"internal": "INTERNAL", "external": "EXTERNAL"},
        default_variant="external",
        context_evaluator=context_func,
    ),
    "wrong-flag": InMemoryFlag(
        flag_key="wrong-flag",
        state="ENABLED",
        variants={"one": "uno", "two": "dos"},
        default_variant="one",
    ),
}

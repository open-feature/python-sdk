from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.provider.in_memory_provider import InMemoryFlag


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
        state=InMemoryFlag.State.ENABLED,
        default_variant="on",
        variants={"on": True, "off": False},
        context_evaluator=None,
    ),
    "string-flag": InMemoryFlag(
        state=InMemoryFlag.State.ENABLED,
        default_variant="greeting",
        variants={"greeting": "hi", "parting": "bye"},
        context_evaluator=None,
    ),
    "integer-flag": InMemoryFlag(
        state=InMemoryFlag.State.ENABLED,
        default_variant="ten",
        variants={"one": 1, "ten": 10},
        context_evaluator=None,
    ),
    "float-flag": InMemoryFlag(
        state=InMemoryFlag.State.ENABLED,
        default_variant="half",
        variants={"tenth": 0.1, "half": 0.5},
        context_evaluator=None,
    ),
    "object-flag": InMemoryFlag(
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
        state=InMemoryFlag.State.ENABLED,
        variants={"internal": "INTERNAL", "external": "EXTERNAL"},
        default_variant="external",
        context_evaluator=context_func,
    ),
    "wrong-flag": InMemoryFlag(
        state="ENABLED",
        variants={"one": "uno", "two": "dos"},
        default_variant="one",
    ),
}

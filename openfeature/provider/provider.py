import warnings

from openfeature.provider import AbstractProvider

__all__ = ["AbstractProvider"]

warnings.warn(
    "openfeature.provider.provider is deprecated, use openfeature.provider instead",
    DeprecationWarning,
    stacklevel=1,
)

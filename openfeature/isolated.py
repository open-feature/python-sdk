"""Factory for creating isolated OpenFeature API instances.

Per specification requirement 1.8.3, this module is intentionally separate
from the global singleton ``openfeature.api`` to reduce the risk of
accidentally creating isolated instances when the singleton is appropriate.

Usage::

    from openfeature.isolated import create_api

    api = create_api()
    api.set_provider(MyProvider())
    client = api.get_client()

Each instance returned by :func:`create_api` maintains its own providers,
evaluation context, hooks, event handlers, and transaction context propagator
— fully independent from the global singleton and from other instances.

A single provider instance should not be registered with more than one API
instance simultaneously (spec requirement 1.8.4).
"""

from openfeature._api import OpenFeatureAPI

__all__ = ["OpenFeatureAPI", "create_api"]


def create_api() -> OpenFeatureAPI:
    """Create a new, independent OpenFeature API instance.

    The returned instance is functionally equivalent to the global singleton
    (``openfeature.api``), but with completely isolated state.

    Returns:
        A new :class:`OpenFeatureAPI` instance.
    """
    return OpenFeatureAPI()

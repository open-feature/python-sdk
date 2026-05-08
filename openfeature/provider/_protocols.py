from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from openfeature.provider import ProviderStatus


@typing.runtime_checkable
class InternalHookProvider(typing.Protocol):
    """Protocol for providers that manage their own provider hook execution.

    Providers implementing this protocol (e.g. MultiProvider) handle provider
    hook lifecycle internally. The client will skip its own provider hook
    invocations and instead delegate to the provider via the set/reset methods.

    The registry will also use get_status() from this protocol instead of its
    own internal status tracking for providers that implement it.

    Implementations must set ``_is_internal_hook_provider = True`` as a class
    attribute. This marker is checked alongside ``isinstance`` to avoid false
    positives from duck-typed objects (e.g. ``Mock``).
    """

    _is_internal_hook_provider: typing.ClassVar[bool]

    def uses_internal_provider_hooks(self) -> bool: ...

    def set_internal_provider_hook_runtime(
        self,
        flag_type: typing.Any,
        client_metadata: typing.Any,
        hook_hints: typing.Any,
    ) -> typing.Any: ...

    def reset_internal_provider_hook_runtime(self, token: typing.Any) -> None: ...

    def get_status(self) -> ProviderStatus: ...

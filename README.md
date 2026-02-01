<!-- markdownlint-disable MD033 -->
<!-- x-hide-in-docs-start -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/open-feature/community/0e23508c163a6a1ac8c0ced3e4bd78faafe627c7/assets/logo/horizontal/white/openfeature-horizontal-white.svg" />
    <img align="center" alt="OpenFeature Logo" src="https://raw.githubusercontent.com/open-feature/community/0e23508c163a6a1ac8c0ced3e4bd78faafe627c7/assets/logo/horizontal/black/openfeature-horizontal-black.svg" />
  </picture>
</p>

<h2 align="center">OpenFeature Python SDK</h2>

<!-- x-hide-in-docs-end -->
<!-- The 'github-badges' class is used in the docs -->
<p align="center" class="github-badges">

  <a href="https://github.com/open-feature/spec/releases/tag/v0.8.0">
    <img alt="Specification" src="https://img.shields.io/static/v1?label=Specification&message=v0.8.0&color=red&style=for-the-badge" />
  </a>

  <!-- x-release-please-start-version -->

  <a href="https://github.com/open-feature/python-sdk/releases/tag/v0.8.4">
    <img alt="Latest version" src="https://img.shields.io/static/v1?label=release&message=v0.8.4&color=blue&style=for-the-badge" />
  </a>

  <!-- x-release-please-end -->
  <br/>
  <a href="https://github.com/open-feature/python-sdk/actions/workflows/merge.yml">
    <img alt="Build status" src="https://github.com/open-feature/python-sdk/actions/workflows/build.yml/badge.svg" />
  </a>

  <a href="https://codecov.io/gh/open-feature/python-sdk">
    <img alt="Codecov" src="https://codecov.io/gh/open-feature/python-sdk/branch/main/graph/badge.svg?token=FQ1I444HB3" />
  </a>

  <a href="https://www.python.org/downloads/">
    <img alt="Min python version" src="https://img.shields.io/badge/python->=3.10-blue.svg" />
  </a>

  <a href="https://www.repostatus.org/#wip">
    <img alt="Repo status" src="https://www.repostatus.org/badges/latest/wip.svg" />
  </a>
</p>
<!-- x-hide-in-docs-start -->

[OpenFeature](https://openfeature.dev) is an open specification that provides a vendor-agnostic, community-driven API for feature flagging that works with your favorite feature flag management tool.

<!-- x-hide-in-docs-end -->

## 🚀 Quick start

### Requirements

- Python 3.10+

### Install

<!---x-release-please-start-version-->

#### Pip install

```bash
pip install openfeature-sdk==0.8.4
```

#### requirements.txt

```bash
openfeature-sdk==0.8.4
```

```python
pip install -r requirements.txt
```

<!---x-release-please-end-->

### Usage

```python
from openfeature import api
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider

# flags defined in memory
my_flags = {
  "v2_enabled": InMemoryFlag("on", {"on": True, "off": False})
}

# configure a provider
api.set_provider(InMemoryProvider(my_flags))

# create a client
client = api.get_client()

# get a bool flag value
flag_value = client.get_boolean_value("v2_enabled", False)
print("Value: " + str(flag_value))
```

## 🌟 Features

| Status | Features                                                            | Description                                                                                                                           |
|--------|---------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| ✅      | [Providers](#providers)                                             | Integrate with a commercial, open source, or in-house feature management tool.                                                        |
| ✅      | [Targeting](#targeting)                                             | Contextually-aware flag evaluation using [evaluation context](https://openfeature.dev/docs/reference/concepts/evaluation-context).    |
| ✅      | [Hooks](#hooks)                                                     | Add functionality to various stages of the flag evaluation life-cycle.                                                                |
| ✅      | [Logging](#logging)                                                 | Integrate with popular logging packages.                                                                                              |
| ✅      | [Domains](#domains)                                                 | Logically bind clients with providers.                                                                                                |
| ✅      | [Eventing](#eventing)                                               | React to state changes in the provider or flag management system.                                                                     |
| ✅      | [Shutdown](#shutdown)                                               | Gracefully clean up a provider during application shutdown.                                                                           |
| ✅      | [Transaction Context Propagation](#transaction-context-propagation) | Set a specific [evaluation context](https://openfeature.dev/docs/reference/concepts/evaluation-context) for a transaction (e.g. an HTTP request or a thread) |
| ✅      | [Extending](#extending)                                             | Extend OpenFeature with custom providers and hooks.                                                                                   |

<sub>Implemented: ✅ | In-progress: ⚠️ | Not implemented yet: ❌</sub>

### Providers

[Providers](https://openfeature.dev/docs/reference/concepts/provider) are an abstraction between a flag management system and the OpenFeature SDK.
Look [here](https://openfeature.dev/ecosystem/?instant_search%5BrefinementList%5D%5Btype%5D%5B0%5D=Provider&instant_search%5BrefinementList%5D%5Btechnology%5D%5B0%5D=Python) for a complete list of available providers.
If the provider you're looking for hasn't been created yet, see the [develop a provider](#develop-a-provider) section to learn how to build it yourself.

Once you've added a provider as a dependency, it can be registered with OpenFeature like this:

```python
from openfeature import api
from openfeature.provider.no_op_provider import NoOpProvider

api.set_provider(NoOpProvider())
open_feature_client = api.get_client()
```

In some situations, it may be beneficial to register multiple providers in the same application.
This is possible using [domains](#domains), which is covered in more detail below.

### Targeting

Sometimes, the value of a flag must consider some dynamic criteria about the application or user, such as the user's location, IP, email address, or the server's location.
In OpenFeature, we refer to this as [targeting](https://openfeature.dev/specification/glossary#targeting).
If the flag management system you're using supports targeting, you can provide the input data using the [evaluation context](https://openfeature.dev/docs/reference/concepts/evaluation-context).

```python
from openfeature.api import (
    get_client,
    get_provider,
    set_provider,
    get_evaluation_context,
    set_evaluation_context,
)

global_context = EvaluationContext(
    targeting_key="targeting_key1", attributes={"application": "value1"}
)
request_context = EvaluationContext(
    targeting_key="targeting_key2", attributes={"email": request.form['email']}
)

## set global context
set_evaluation_context(global_context)

# merge second context
client = get_client(name="No-op Provider")
client.get_string_value("email", "fallback", request_context)
```

### Hooks

[Hooks](https://openfeature.dev/docs/reference/concepts/hooks) allow for custom logic to be added at well-defined points of the flag evaluation life-cycle.
Look [here](https://openfeature.dev/ecosystem/?instant_search%5BrefinementList%5D%5Btype%5D%5B0%5D=Hook&instant_search%5BrefinementList%5D%5Btechnology%5D%5B0%5D=Python) for a complete list of available hooks.
If the hook you're looking for hasn't been created yet, see the [develop a hook](#develop-a-hook) section to learn how to build it yourself.

Once you've added a hook as a dependency, it can be registered at the global, client, or flag invocation level.

```python
from openfeature.api import add_hooks
from openfeature.flag_evaluation import FlagEvaluationOptions

# set global hooks at the API-level
add_hooks([MyHook()])

# or configure them in the client
client = OpenFeatureClient()
client.add_hooks([MyHook()])

# or at the invocation-level
options = FlagEvaluationOptions(hooks=[MyHook()])
client.get_boolean_flag("my-flag", False, flag_evaluation_options=options)
```
### Tracking

The [tracking API](https://openfeature.dev/specification/sections/tracking/) allows you to use OpenFeature abstractions and objects to associate user actions with feature flag evaluations.
This is essential for robust experimentation powered by feature flags.
For example, a flag enhancing the appearance of a UI component might drive user engagement to a new feature; to test this hypothesis, telemetry collected by a [hook](#hooks) or [provider](#providers) can be associated with telemetry reported in the client's `track` function.

```python
// initilize a client
client := api.get_client()

// trigger tracking event action
client.Track(
    'visited-promo-page', 
    EvaluationContext{}, 
    openfeature.TrackingEventDetails(99.77).add("currencyCode", "USD"),
    )
```

Note that some providers may not support tracking; check the documentation for your provider for more information.

### Logging

The OpenFeature SDK logs to the `openfeature` logger using the `logging` package from the Python Standard Library.

### Domains

Clients can be assigned to a domain.
A domain is a logical identifier which can be used to associate clients with a particular provider.
If a domain has no associated provider, the global provider is used.

```python
from openfeature import api

# Registering the default provider
api.set_provider(MyProvider());
# Registering a provider to a domain
api.set_provider(MyProvider(), "my-domain");

# A client bound to the default provider
default_client = api.get_client();
# A client bound to the MyProvider provider
domain_scoped_client = api.get_client("my-domain");
```

Domains can be defined on a provider during registration.
For more details, please refer to the [providers](#providers) section.

### Eventing

Events allow you to react to state changes in the provider or underlying flag management system, such as flag definition changes, provider readiness, or error conditions. Initialization events (PROVIDER_READY on success, PROVIDER_ERROR on failure) are dispatched for every provider. Some providers support additional events, such as PROVIDER_CONFIGURATION_CHANGED.

Please refer to the documentation of the provider you're using to see what events are supported.

```python
from openfeature import api
from openfeature.provider import ProviderEvent

def on_provider_ready(event_details: EventDetails):
    print(f"Provider {event_details.provider_name} is ready")

api.add_handler(ProviderEvent.PROVIDER_READY, on_provider_ready)

client = api.get_client()

def on_provider_ready(event_details: EventDetails):
    print(f"Provider {event_details.provider_name} is ready")

client.add_handler(ProviderEvent.PROVIDER_READY, on_provider_ready)
```

### Transaction Context Propagation

Transaction context is a container for transaction-specific evaluation context (e.g. user id, user agent, IP).
Transaction context can be set where specific data is available (e.g. an auth service or request handler) and by using the transaction context propagator it will automatically be applied to all flag evaluations within a transaction (e.g. a request or thread).

You can implement a different transaction context propagator by implementing the `TransactionContextPropagator` class exported by the OpenFeature SDK.
In most cases you can use `ContextVarsTransactionContextPropagator` as it works for `threads` and `asyncio` using [Context Variables](https://peps.python.org/pep-0567/).

The following example shows a **multithreaded** Flask application using transaction context propagation to propagate the request ip and user id into request scoped transaction context.

```python
from flask import Flask, request
from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context import ContextVarsTransactionContextPropagator

# Initialize the Flask app
app = Flask(__name__)

# Set the transaction context propagator
api.set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

# Middleware to set the transaction context
# You can call api.set_transaction_context anywhere you have information,
# you want to have available in the code-paths below the current one.
@app.before_request
def set_request_transaction_context():
  ip = request.headers.get("X-Forwarded-For", request.remote_addr)
  user_id = request.headers.get("User-Id")  # Assuming we're getting the user ID from a header
  evaluation_context = EvaluationContext(targeting_key=user_id, attributes={"ipAddress": ip})
  api.set_transaction_context(evaluation_context)

def create_response() -> str:
  # This method can be anywhere in our code.
  # The feature flag evaluation will automatically contain the transaction context merged with other context
  new_response = api.get_client().get_string_value("response-message", "Hello User!")
  return f"Message from server: {new_response}"

# Example route where we use the transaction context
@app.route('/greeting')
def some_endpoint():
  return create_response()
```

This also works for asyncio based implementations e.g. FastApi as seen in the following example:

```python
from fastapi import FastAPI, Request
from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from openfeature.transaction_context import ContextVarsTransactionContextPropagator

# Initialize the FastAPI app
app = FastAPI()

# Set the transaction context propagator
api.set_transaction_context_propagator(ContextVarsTransactionContextPropagator())

# Middleware to set the transaction context
@app.middleware("http")
async def set_request_transaction_context(request: Request, call_next):
    ip = request.headers.get("X-Forwarded-For", request.client.host)
    user_id = request.headers.get("User-Id")  # Assuming we're getting the user ID from a header
    evaluation_context = EvaluationContext(targeting_key=user_id, attributes={"ipAddress": ip})
    api.set_transaction_context(evaluation_context)
    response = await call_next(request)
    return response

def create_response() -> str:
    # This method can be located anywhere in our code.
    # The feature flag evaluation will automatically include the transaction context merged with other context.
    new_response = api.get_client().get_string_value("response-message", "Hello User!")
    return f"Message from server: {new_response}"

# Example route where we use the transaction context
@app.get('/greeting')
async def some_endpoint():
    return create_response()
```

### Asynchronous Feature Retrieval

The OpenFeature API supports asynchronous calls, enabling non-blocking feature evaluations for improved performance, especially useful in concurrent or latency-sensitive scenarios. If a provider *hasn't* implemented asynchronous calls, the client can still be used asynchronously, but calls will be blocking (synchronous).

```python
import asyncio
from openfeature import api
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider

my_flags = { "v2_enabled": InMemoryFlag("on", {"on": True, "off": False}) }
api.set_provider(InMemoryProvider(my_flags))
client = api.get_client()
flag_value = await client.get_boolean_value_async("v2_enabled", False) # API calls are suffixed by _async

print("Value: " + str(flag_value))
```

See the [develop a provider](#develop-a-provider) for how to support asynchronous functionality in providers.

### Shutdown

The OpenFeature API provides a shutdown function to perform a cleanup of all registered providers. This should only be called when your application is in the process of shutting down.

```python
from openfeature import api

api.shutdown()
```

## Extending

### Develop a provider

To develop a provider, you need to create a new project and include the OpenFeature SDK as a dependency.
This can be a new repository or included in [the existing contrib repository](https://github.com/open-feature/python-sdk-contrib) available under the OpenFeature organization.
You’ll then need to write the provider by implementing the `AbstractProvider` class exported by the OpenFeature SDK.

```python
from typing import List, Optional, Union

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.hook import Hook
from openfeature.provider import AbstractProvider, Metadata

class MyProvider(AbstractProvider):
    def get_metadata(self) -> Metadata:
        ...

    def get_provider_hooks(self) -> List[Hook]:
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        ...

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        ...

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        ...

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        ...

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[dict, list],
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Union[dict, list]]:
        ...
```

Providers can also be extended to support async functionality.
To support add asynchronous calls to a provider:

- Implement the `AbstractProvider` as shown above.
- Define asynchronous calls for each data type.

```python
class MyProvider(AbstractProvider):
    ...
    async def resolve_boolean_details_async(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        ...

    async def resolve_string_details_async(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        ...

    async def resolve_integer_details_async(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        ...

    async def resolve_float_details_async(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        ...

    async def resolve_object_details_async(
        self,
        flag_key: str,
        default_value: Union[dict, list],
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Union[dict, list]]:
        ...

```

> Built a new provider? [Let us know](https://github.com/open-feature/openfeature.dev/issues/new?assignees=&labels=provider&projects=&template=document-provider.yaml&title=%5BProvider%5D%3A+) so we can add it to the docs!

### Develop a hook

To develop a hook, you need to create a new project and include the OpenFeature SDK as a dependency.
This can be a new repository or included in [the existing contrib repository](https://github.com/open-feature/python-sdk-contrib) available under the OpenFeature organization.
Implement your own hook by creating a hook that inherits from the `Hook` class.
Any of the evaluation life-cycle stages (`before`/`after`/`error`/`finally_after`) can be override to add the desired business logic.

```python
from openfeature.hook import Hook

class MyHook(Hook):
    def after(self, hook_context: HookContext, details: FlagEvaluationDetails, hints: dict):
        print("This runs after the flag has been evaluated")

```

> Built a new hook? [Let us know](https://github.com/open-feature/openfeature.dev/issues/new?assignees=&labels=hook&projects=&template=document-hook.yaml&title=%5BHook%5D%3A+) so we can add it to the docs!

<!-- x-hide-in-docs-start -->

## ⭐️ Support the project

- Give this repo a ⭐️!
- Follow us on social media:
  - Twitter: [@openfeature](https://twitter.com/openfeature)
  - LinkedIn: [OpenFeature](https://www.linkedin.com/company/openfeature/)
- Join us on [Slack](https://cloud-native.slack.com/archives/C0344AANLA1)
- For more, check out our [community page](https://openfeature.dev/community/)

## 🤝 Contributing

Interested in contributing? Great, we'd love your help! To get started, take a look at the [CONTRIBUTING](CONTRIBUTING.md) guide.

### Thanks to everyone who has already contributed

<a href="https://github.com/open-feature/python-sdk/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=open-feature/python-sdk" alt="Pictures of the folks who have contributed to the project" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

<!-- x-hide-in-docs-end -->

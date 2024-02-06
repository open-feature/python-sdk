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

  <a href="https://github.com/open-feature/spec/releases/tag/v0.5.2">
    <img alt="Specification" src="https://img.shields.io/static/v1?label=Specification&message=v0.5.2&color=red&style=for-the-badge" />
  </a>

  <!-- x-release-please-start-version -->

  <a href="https://github.com/open-feature/python-sdk/releases/tag/v0.4.2">
    <img alt="Latest version" src="https://img.shields.io/static/v1?label=release&message=v0.4.2&color=blue&style=for-the-badge" />
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
    <img alt="Min python version" src="https://img.shields.io/badge/python->=3.8-blue.svg" />
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

- Python 3.8+

### Install

<!---x-release-please-start-version-->

#### Pip install

```bash
pip install openfeature-sdk==0.4.2
```

#### requirements.txt

```bash
openfeature-sdk==0.4.2
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

| Status | Features                        | Description                                                                                                                        |
| ------ | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| ✅      | [Providers](#providers)         | Integrate with a commercial, open source, or in-house feature management tool.                                                     |
| ✅      | [Targeting](#targeting)         | Contextually-aware flag evaluation using [evaluation context](https://openfeature.dev/docs/reference/concepts/evaluation-context). |
| ✅      | [Hooks](#hooks)                 | Add functionality to various stages of the flag evaluation life-cycle.                                                             |
| ✅      | [Logging](#logging)             | Integrate with popular logging packages.                                                                                           |
| ❌      | [Named clients](#named-clients) | Utilize multiple providers in a single application.                                                                                |
| ❌      | [Eventing](#eventing)           | React to state changes in the provider or flag management system.                                                                  |
| ✅      | [Shutdown](#shutdown)           | Gracefully clean up a provider during application shutdown.                                                                        |
| ✅      | [Extending](#extending)         | Extend OpenFeature with custom providers and hooks.                                                                                |

<sub>Implemented: ✅ | In-progress: ⚠️ | Not implemented yet: ❌</sub>

### Providers

[Providers](https://openfeature.dev/docs/reference/concepts/provider) are an abstraction between a flag management system and the OpenFeature SDK.
Look [here](https://openfeature.dev/ecosystem?instant_search%5BrefinementList%5D%5Btype%5D%5B0%5D=Provider&instant_search%5BrefinementList%5D%5Btechnology%5D%5B0%5D=python) for a complete list of available providers.
If the provider you're looking for hasn't been created yet, see the [develop a provider](#develop-a-provider) section to learn how to build it yourself.

Once you've added a provider as a dependency, it can be registered with OpenFeature like this:

```python
from openfeature import api
from openfeature.provider.no_op_provider import NoOpProvider

api.set_provider(NoOpProvider())
open_feature_client = api.get_client()
```

<!-- In some situations, it may be beneficial to register multiple providers in the same application.
This is possible using [named clients](#named-clients), which is covered in more detail below. -->

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
Look [here](https://openfeature.dev/ecosystem/?instant_search%5BrefinementList%5D%5Btype%5D%5B0%5D=Hook&instant_search%5BrefinementList%5D%5Btechnology%5D%5B0%5D=python) for a complete list of available hooks.
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

### Logging

The OpenFeature SDK logs to the `openfeature` logger using the `logging` package from the Python Standard Library.

### Named clients

Named clients are not yet available in the Python SDK. Progress on this feature can be tracked [here](https://github.com/open-feature/python-sdk/issues/125).

### Eventing

Events are not yet available in the Python SDK. Progress on this feature can be tracked [here](https://github.com/open-feature/python-sdk/issues/125).

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
from typing import List, Optional

from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.provider.provider import AbstractProvider

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

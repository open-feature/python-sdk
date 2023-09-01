<!-- markdownlint-disable MD033 -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/open-feature/community/0e23508c163a6a1ac8c0ced3e4bd78faafe627c7/assets/logo/horizontal/white/openfeature-horizontal-white.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/open-feature/community/0e23508c163a6a1ac8c0ced3e4bd78faafe627c7/assets/logo/horizontal/black/openfeature-horizontal-black.svg">
    <img align="center" alt="OpenFeature Logo">
  </picture>
</p>

<h2 align="center">OpenFeature Python SDK</h2>

[![PyPI version](https://badge.fury.io/py/openfeature-sdk.svg)](https://badge.fury.io/py/openfeature-sdk)
![Python 3.8+](https://img.shields.io/badge/python->=3.8-blue.svg)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Specification](https://img.shields.io/static/v1?label=Specification&message=v0.3.0&color=red)](https://github.com/open-feature/spec/tree/v0.3.0)
[![on-merge](https://github.com/open-feature/python-sdk/actions/workflows/merge.yml/badge.svg)](https://github.com/open-feature/python-sdk/actions/workflows/merge.yml)
[![codecov](https://codecov.io/gh/open-feature/python-sdk/branch/main/graph/badge.svg?token=FQ1I444HB3)](https://codecov.io/gh/open-feature/python-sdk)

> ⚠️ Development is in progress, but there's not a stable release available. ⚠️

This is the Python implementation of [OpenFeature](https://openfeature.dev), a vendor-agnostic abstraction library for evaluating feature flags.

We support multiple data types for flags (numbers, strings, booleans, objects) as well as hooks, which can alter the lifecycle of a flag evaluation.

This library is intended to be used in server-side contexts and has not been evaluated for use in mobile devices.

## 🔍 Requirements:

- Python 3.8+

## 📦 Installation:

### Add it to your build

<!---x-release-please-start-version-->

Pip install

```bash
pip install openfeature-sdk==0.1.0
```

requirements.txt

```bash
openfeature-sdk==0.1.0
```

```python
pip install requirements.txt
```

<!---x-release-please-end-->

## 🌟 Features:

- support for various backend [providers](https://openfeature.dev/docs/reference/concepts/provider)
- easy integration and extension via [hooks](https://openfeature.dev/docs/reference/concepts/hooks)
- bool, string, numeric, and object flag types
- [context-aware](https://openfeature.dev/docs/reference/concepts/evaluation-context) evaluation

## 🚀 Usage:

### Configure it

In order to use the sdk there is some minor configuration. Follow the script below:

```python
from open_feature import api
from open_feature.provider.no_op_provider import NoOpProvider

api.set_provider(NoOpProvider())
open_feature_client = api.get_client()
```

### Basics:

While Boolean provides the simplest introduction, we offer a variety of flag types.

```python
# Depending on the flag type, use one of the methods below
flag_key = "PROVIDER_FLAG"
boolean_result = open_feature_client.get_boolean_value(key=flag_key,default_value=False)
integer_result = open_feature_client.get_integer_value(key=flag_key,default_value=-1)
float_result = open_feature_client.get_float_value(key=flag_key,default_value=-1)
string_result = open_feature_client.get_string_value(key=flag_key,default_value="")
object_result = open_feature_client.get_object_value(key=flag_key,default_value={})
```

You can also bind a provider to a specific client by name instead of setting that provider globally:

```python

api.set_provider(NoOpProvider())
```

Each provider class may have further setup required i.e. secret keys, environment variables etc

### Context-aware evaluation:

Sometimes the value of a flag must take into account some dynamic criteria about the application or user, such as the user location, IP, email address, or the location of the server.
In OpenFeature, we refer to this as [`targeting`](https://openfeature.dev/specification/glossary#targeting).
If the flag system you're using supports targeting, you can provide the input data using the `EvaluationContext`.

```python
from open_feature.api import (
    get_client,
    get_provider,
    set_provider
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
set_evaluation_context(first_context)

# merge second context
client = get_client(name="No-op Provider", version="0.5.2")
client.get_string_value("email", None, request_context)

```

### Events

TBD (See Issue [#131](https://github.com/open-feature/python-sdk/issues/131))

### Providers:

To develop a provider, you need to create a new project and include the OpenFeature SDK as a dependency. This can be a new repository or included in [the existing contrib repository](https://github.com/open-feature/python-sdk-contrib) available under the OpenFeature organization. Finally, you’ll then need to write the provider itself. This can be accomplished by implementing the `Provider` interface exported by the OpenFeature SDK.

See [here](https://openfeature.dev/ecosystem) for a catalog of available providers.

### Hooks:

A hook is a mechanism that allows for adding arbitrary behavior at well-defined points of the flag evaluation life-cycle. Use cases include validating the resolved flag value, modifying or adding data to the evaluation context, logging, telemetry, and tracking.

```python
from open_feature.hook import Hook

class MyHook(Hook):
    def after(self, hook_context: HookContext, details: FlagEvaluationDetails, hints: dict):
        print("This runs after the flag has been evaluated")


# set global hooks at the API-level
from open_feature.api import add_hooks
add_hooks([MyHook()])

# or configure them in the client
client = OpenFeatureClient()
client.add_hooks([MyHook()])
```

See [here](https://openfeature.dev/ecosystem) for a catalog of available hooks.

### Logging:

TBD

## ⭐️ Support the project

- Give this repo a ⭐️!
- Follow us on social media:
  - Twitter: [@openfeature](https://twitter.com/openfeature)
  - LinkedIn: [OpenFeature](https://www.linkedin.com/company/openfeature/)
- Join us on [Slack](https://cloud-native.slack.com/archives/C0344AANLA1)
- For more check out our [community page](https://openfeature.dev/community/)

## 🤝 Contributing

Interested in contributing? Great, we'd love your help! To get started, take a look at the [CONTRIBUTING](CONTRIBUTING.md) guide.

### Thanks to everyone that has already contributed

<!-- TODO: update with correct repo -->
<a href="https://github.com/open-feature/python-sdk/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=open-feature/python-sdk" alt="Pictures of the folks who have contributed to the project" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

## Contacting us

We hold regular meetings which you can see [here](https://github.com/open-feature/community/#meetings-and-events).

We are also present on the `#openfeature` channel in the [CNCF slack](https://slack.cncf.io/).

## 📜 License

[Apache License 2.0](LICENSE)

<!-- TODO: add FOSSA widget -->

[openfeature-website]: https://openfeature.dev

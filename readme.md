# Open Feature SDK for Python
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)


This is the Python implementation of [OpenFeature](https://openfeature.dev), a vendor-agnostic abstraction library for evaluating feature flags.

We support multiple data types for flags (numbers, strings, booleans, objects) as well as  hooks, which can alter the lifecycle of a flag evaluation.

This library is intended to be used in server-side contexts and has not been evaluated for use in mobile devices.


## Usage
While Boolean provides the simplest introduction, we offer a variety of flag types.
```python
# Depending on the flag type, use one of the methods below
flag_key = "PROVIDER_FLAG"
boolean_result = open_feature_client.get_boolean_value(key=flag_key,default_value=False)
number_result = open_feature_client.get_number_value(key=flag_key,default_value=-1)
string_result = open_feature_client.get_string_value(key=flag_key,default_value="")
object_result = open_feature_client.get_object_value(key=flag_key,default_value={})
```
Each provider class may have further setup required i.e. secret keys, environment variables etc

## Requirements
- Python 3.8+

## Installation
### Add it to your build
Pip install
```bash
pip install python-open-feature-sdk==0.0.1
```

requirements.txt
```bash
python-open-feature-sdk==0.0.1
```
```python
pip install requirements.txt
```

### Configure it
In order to use the sdk there is some minor configuration. Follow the script below:

```python
from open_feature import open_feature_api

open_feature_api.set_provider(NoOpProvider())
open_feature_client = open_feature_api.get_client()
```

## Contacting us
We hold regular meetings which you can see [here](https://github.com/open-feature/community/#meetings-and-events).

We are also present on the `#openfeature` channel in the [CNCF slack](https://slack.cncf.io/).

## Contributors

Thanks so much to our contributors.

<a href="https://github.com/open-feature/python-sdk/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=open-feature/python-sdk" />
</a>


Made with [contrib.rocks](https://contrib.rocks).
# Contributing

## Development

### System Requirements

Python 3.9 and above are required.

### Target version(s)

Python 3.9 and above are supported by the SDK.

### Installation and Dependencies

We use [uv](https://github.com/astral-sh/uv) for fast Python package management and dependency resolution.

To install uv, follow the [installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/open-feature/python-sdk.git
   cd python-sdk
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

### Testing

Run tests:
```bash
uv run test --frozen
```

### Coverage

Run tests with a coverage report:
```bash
uv run cov --frozen
```

### End-to-End Tests

Run e2e tests with behave:
```bash
uv run e2e --frozen
```

### Pre-commit

Run pre-commit hooks
```bash
uv run precommit --frozen
```


### Integration tests

These are planned once the SDK has been stabilized and a Flagd provider implemented. At that point, we will utilize the [gherkin integration tests](https://github.com/open-feature/test-harness/blob/main/features/evaluation.feature) to validate against a live, seeded Flagd instance.

### Packaging

We publish to the PyPI repository, where you can find this package at [openfeature-sdk](https://pypi.org/project/openfeature-sdk/).

## Pull Request

All contributions to the OpenFeature project are welcome via GitHub pull requests.

To create a new PR, you will need to first fork the GitHub repository and clone upstream.

```bash
git clone https://github.com/open-feature/python-sdk.git openfeature-python-sdk
```

Navigate to the repository folder

```bash
cd openfeature-python-sdk
```

Add your fork as an origin

```bash
git remote add fork https://github.com/YOUR_GITHUB_USERNAME/python-sdk.git
```

Ensure your development environment is all set up by building and testing

```bash
uv run test --frozen
```

To start working on a new feature or bugfix, create a new branch and start working on it.

```bash
git checkout -b feat/NAME_OF_FEATURE
# Make your changes
git commit
git push fork feat/NAME_OF_FEATURE
```

Open a pull request against the main python-sdk repository.

### How to Receive Comments

- If the PR is not ready for review, please mark it as
  [`draft`](https://github.blog/2019-02-14-introducing-draft-pull-requests/).
- Make sure all required CI checks are clear.
- Submit small, focused PRs addressing a single concern/issue.
- Make sure the PR title reflects the contribution.
- Write a summary that explains the change.
- Include usage examples in the summary, where applicable.

### How to Get PRs Merged

A PR is considered to be **ready to merge** when:

- Major feedback is resolved.
- Urgent fix can take exception as long as it has been actively communicated.

Any Maintainer can merge the PR once it is **ready to merge**. Note, that some
PRs may not be merged immediately if the repo is in the process of a release and
the maintainers decided to defer the PR to the next release train.

If a PR has been stuck (e.g. there are lots of debates and people couldn't agree
on each other), the owner should try to get people aligned by:

- Consolidating the perspectives and putting a summary in the PR. It is
  recommended to add a link into the PR description, which points to a comment
  with a summary in the PR conversation.
- Tagging domain experts (by looking at the change history) in the PR asking
  for suggestion.
- Reaching out to more people on the [CNCF OpenFeature Slack channel](https://cloud-native.slack.com/archives/C0344AANLA1).
- Stepping back to see if it makes sense to narrow down the scope of the PR or
  split it up.
- If none of the above worked and the PR has been stuck for more than 2 weeks,
  the owner should bring it to the OpenFeatures [meeting](README.md#contributing).

## Design Choices

As with other OpenFeature SDKs, python-sdk follows the
[openfeature-specification](https://github.com/open-feature/spec).

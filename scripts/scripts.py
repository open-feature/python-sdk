# ruff: noqa: S602, S607
import subprocess


def test():
    """Run pytest tests."""
    subprocess.run("pytest tests", shell=True, check=True)


def test_cov():
    """Run tests with coverage."""
    subprocess.run("coverage run -m pytest tests", shell=True, check=True)


def cov_report():
    """Generate coverage report."""
    subprocess.run("coverage xml", shell=True, check=True)


def cov():
    """Run tests with coverage and generate report."""
    test_cov()
    cov_report()


def e2e():
    """Run end-to-end tests."""
    subprocess.run("git submodule update --init --recursive", shell=True, check=True)
    subprocess.run(
        "cp spec/specification/assets/gherkin/* tests/features/", shell=True, check=True
    )
    subprocess.run("behave tests/features/", shell=True, check=True)
    subprocess.run("rm tests/features/*.feature", shell=True, check=True)


def precommit():
    """Run pre-commit hooks."""
    subprocess.run("uv run pre-commit run --all-files", shell=True, check=True)

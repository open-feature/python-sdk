# ruff: noqa: S607
import shutil
import subprocess
from pathlib import Path


def test():
    """Run pytest tests."""
    subprocess.run(["pytest", "tests"], check=True)


def test_cov():
    """Run tests with coverage."""
    subprocess.run(["coverage", "run", "-m", "pytest", "tests"], check=True)


def cov_report():
    """Generate coverage report."""
    subprocess.run(["coverage", "xml"], check=True)


def cov():
    """Run tests with coverage and generate report."""
    test_cov()
    cov_report()


def e2e():
    """Run end-to-end tests."""
    source_dir = Path("spec/specification/assets/gherkin")
    dest_dir = Path("tests/features")

    subprocess.run(["git", "submodule", "update", "--init", "--recursive"], check=True)

    for file in source_dir.glob("*"):
        if file.is_file():
            shutil.copy(file, dest_dir)

    subprocess.run(["behave", "tests/features/"], check=True)

    for feature_file in dest_dir.glob("*.feature"):
        feature_file.unlink()


def precommit():
    """Run pre-commit hooks."""
    subprocess.run(["uv", "run", "pre-commit", "run", "--all-files"], check=True)

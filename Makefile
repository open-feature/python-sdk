VENV_NAME ?= .venv
VENV_ACTIVATE = . $(VENV_NAME)/bin/activate

.DEFAULT_GOAL := help

.PHONY: init
init: venv

.PHONY: help
help:
	@echo "Targets:"
	@echo "  requirements    Installs dependencies"
	@echo "  venv            Creates a virtual environment and install dependencies"
	@echo "  test            Run pytest on the tests/ directory"
	@echo "  lint            Check code with flake8 and black"
	@echo "  format          Format code with black"

.PHONY: requirements
requirements:
	$(VENV_ACTIVATE); pip install -r requirements.txt

.PHONY: venv
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	$(VENV_ACTIVATE); pip install -r requirements.txt

.PHONY: test
test: venv
	$(VENV_ACTIVATE); pytest tests/

test-harness:
	git submodule update --init

.PHONY: lint
lint: venv
	$(VENV_ACTIVATE); flake8 .
	$(VENV_ACTIVATE); isort .
	$(VENV_ACTIVATE); black --check .

.PHONY: format
format: venv
	$(VENV_ACTIVATE); black .

.PHONY: e2e
e2e: venv test-harness
	# NOTE: only the evaluation feature is run for now
	cp test-harness/features/evaluation.feature tests/features/
	$(VENV_ACTIVATE); behave tests/features/
	rm tests/features/*.feature

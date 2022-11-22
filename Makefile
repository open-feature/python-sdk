VENV = . .venv/bin/activate

.PHONY: all
all: lint test

.PHONY: init
init: .venv

.venv: requirements-dev.txt
	test -d .venv || python -m virtualenv .venv
	$(VENV); pip install -Ur requirements-dev.txt

.PHONY: test
test: .venv
	$(VENV); pytest

.PHONY: lint
lint: .venv
	$(VENV); black .
	$(VENV); flake8 .
	$(VENV); isort .

.PHONY: clean
clean:
	@rm -rf .venv
	@find -iname "*.pyc" -delete

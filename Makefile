VENV = . .venv/bin/activate

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

.PHONY: all
all: lint test

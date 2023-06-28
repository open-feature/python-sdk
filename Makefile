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
ifdef TEST
	$(VENV); pytest $(TEST)
else
	$(VENV); pytest
endif

.PHONY: lint
lint: .venv
	$(VENV); black .
	$(VENV); flake8 .
	$(VENV); isort .

.PHONY: clean
clean:
	@rm -rf .venv
	@find -iname "*.pyc" -delete

.PHONY: e2e
e2e: .venv
	# NOTE: only the evaluation feature is run for now
	cp test-harness/features/evaluation.feature tests/features/
	behave tests/features/
	rm tests/features/*.feature

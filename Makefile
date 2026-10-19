PYTHON = .venv/bin/python
MAP ?=
ARGS ?=

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

run:
	@$(PYTHON) main.py $(if $(MAP),"$(MAP)") $(ARGS)

debug:
	$(PYTHON) -m pdb main.py $(if $(MAP),"$(MAP)") $(ARGS)

clean:
	find src -type d -name "__pycache__" -prune -exec rm -rf {} +
	find src -type f -name "*.py[co]" -delete
	rm -rf __pycache__ .mypy_cache .pytest_cache
	rm -f *.pyc *.pyo

clean-venv:
	rm -rf .venv

lint:
	$(PYTHON) -m flake8 . --extend-exclude=.venv
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 . --extend-exclude=.venv
	$(PYTHON) -m mypy . --strict

.PHONY: install run debug clean clean-venv lint lint-strict

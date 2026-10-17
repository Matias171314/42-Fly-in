PYTHON = .venv/bin/python
MAP ?=
ARGS ?=

.PHONY: install run debug clean lint lint-strict
install:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt
run:
	@$(PYTHON) main.py $(if $(MAP),"$(MAP)") $(ARGS)
debug:
	$(PYTHON) -m pdb main.py $(if $(MAP),"$(MAP)") $(ARGS)
clean:
	find . -path './.venv' -prune -o -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -exec rm -rf {} +
lint:
	.venv/bin/flake8 .
	.venv/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
lint-strict:
	.venv/bin/flake8 .
	.venv/bin/mypy . --strict

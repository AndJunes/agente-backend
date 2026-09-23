PYTHON ?= python

.PHONY: install run lint format typecheck demo clean runner-image

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m mirag serve

# The per-project execution sandbox `DockerCodeRunner` launches containers from
# (MIRAG_EXECUTION_BACKEND=docker). Built once, by hand: never on a request path, since a cold
# `pip install` mid-certification would stall a real user for minutes.
runner-image:
	docker build -f docker/runner.Dockerfile -t mirag-runner:latest .

lint:
	$(PYTHON) -m ruff check src benchmarks scripts

format:
	$(PYTHON) -m ruff check --fix src benchmarks scripts

typecheck:
	$(PYTHON) -m mypy

demo:
	$(PYTHON) -m mirag demo all

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('.pytest_cache', '.ruff_cache', '.mypy_cache', 'build', 'dist')]"

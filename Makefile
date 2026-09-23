PYTHON ?= python

.PHONY: install run run-manager lint format test typecheck check demo clean clean-deps runner-image

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m mirag serve

# Backend and PM, one process, one port — see src/mirag_manager. What used to be two
# terminals (`mirag serve` and `mirag_pm serve`, each remembering its own port and token) is
# one command; the agents stay exactly as isolated as they were standalone, only the transport
# is shared.
run-manager:
	$(PYTHON) -m mirag_manager serve

# The per-project execution sandbox `DockerCodeRunner` launches containers from
# (MIRAG_EXECUTION_BACKEND=docker). Built once, by hand: never on a request path, since a cold
# `pip install` mid-certification would stall a real user for minutes.
runner-image:
	docker build -f docker/runner.Dockerfile -t mirag-runner:latest .

lint:
	$(PYTHON) -m ruff check src benchmarks scripts

format:
	$(PYTHON) -m ruff check --fix src benchmarks scripts

test:
	$(PYTHON) -m pytest

typecheck:
	$(PYTHON) -m mypy

# Everything that has to be green before a change ships. `install` first, so a fresh
# checkout is one command away from an answer rather than three failures away from one.
check: install lint typecheck test

demo:
	$(PYTHON) -m mirag demo all

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('.pytest_cache', '.ruff_cache', '.mypy_cache', 'build', 'dist')]"

# The Docker volumes generated projects' dependencies were installed into. They are cached on
# purpose — a second project asking for the same FastAPI installs nothing — so they are NOT
# removed by `clean`, and nothing removes them automatically. The label is written by
# `DockerInstaller.create_argv`; a volume still in use by a container is left alone.
clean-deps:
	docker volume ls --filter label=mirag.deps=1 -q | xargs -r docker volume rm

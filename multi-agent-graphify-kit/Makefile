PYTHON ?= python3
TASK ?= TASK-001
GOAL ?= GOAL-001

.PHONY: test compile skill-check graph sync validate goal-check scope-check all package clean

test:
	$(PYTHON) scripts/run_tests.py

compile:
	$(PYTHON) -m compileall -q src scripts skills/cogem/scripts

skill-check:
	$(PYTHON) scripts/cogem.py skill-check --root .

graph:
	$(PYTHON) scripts/cogem.py graph --root .

sync:
	$(PYTHON) scripts/cogem.py sync --root .

validate:
	$(PYTHON) scripts/cogem.py validate --root .

goal-check:
	$(PYTHON) scripts/cogem.py goal-check $(GOAL) --root .

scope-check:
	$(PYTHON) scripts/cogem.py scope-check $(TASK) --root .

all: test compile skill-check
	$(PYTHON) scripts/cogem.py all --root .

package:
	$(PYTHON) scripts/package_kit.py --root . --output ../multi-agent-graphify-kit-v5.0.0.zip

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .graph build dist *.egg-info

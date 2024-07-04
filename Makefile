VENVDIR ?= venv
VENV ?= $(VENVDIR)/bin
VENV_MARKER := .makefile_venv
PY := python3

default: peering

.PHONY: venv
venv: $(VENVDIR)/$(VENV_MARKER)

.PHONY: venv-clean
venv-clean:
	-rm -rf "$(VENVDIR)"

$(VENV):
	$(PY) -m venv $(VENVDIR)

$(VENVDIR)/$(VENV_MARKER): requirements.txt | $(VENV)
	$(VENV)/pip install -r requirements.txt
	touch $(VENVDIR)/$(VENV_MARKER)

SHELL:=/bin/bash

##
# TASKS
##

.PHONY: peering
peering: venv  ## make peering # Interactively create a new peerng
	@python interactive.py

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

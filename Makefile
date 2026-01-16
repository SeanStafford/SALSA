.PHONY: help venv install install-dev clean lint format test test-all test-unit test-integration test-cov recent

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = salsa
PYTHON_VERSION = 3.9
PYTHON_INTERPRETER = python3

#################################################################################
# INSTALLATION COMMANDS                                                         #
#################################################################################

## Create virtual environment
venv:
	$(PYTHON_INTERPRETER) -m venv .venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

## Install base dependencies
install:
	pip install -e .

## Install development dependencies
install-dev:
	pip install -e ".[dev]"

#################################################################################
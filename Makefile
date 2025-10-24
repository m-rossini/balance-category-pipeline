# Makefile for Development Container

# Define variables
PROJECT_NAME = balance
PACKAGE_NAME = balance


# Run tests
PYTEST_ADDOPTS="-s"
test:
	PYTHONPATH=src poetry run pytest tests/

# Run tests with coverage (requires pytest-cov in dev dependencies)
coverage:
	PYTHONPATH=src poetry run pytest --cov=src --cov-report=term-missing --cov-report=html:htmlcov tests/

# Lint code
lint:
	poetry run pylint src/${PACKAGE_NAME}

# Format code
format:
	poetry run black src/${PACKAGE_NAME}
	poetry run isort src/${PACKAGE_NAME}

# Install dependencies
install:
	poetry install

# Update dependencies
update:
	poetry update

.PHONY: load run test lint format install update coverage

# Default workflow and log level for running workflows (overridable)
WORKFLOW ?= bank_transaction_analysis
LOG_LEVEL ?= INFO

# Run the summaries workflow using the workflow runner
transactions:
	PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow $(WORKFLOW) --log-level $(LOG_LEVEL)

ai-categorize:
	PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow ai_categorization --log-level $(LOG_LEVEL) 

.PHONY: transactions ai-categorize

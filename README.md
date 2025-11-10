# Balance - Bank Transaction Analysis Pipeline

A comprehensive data processing pipeline for analyzing and categorizing bank transactions using Python, Poetry, and containerized development with Podman.

## Overview

Balance is a modular pipeline system that processes bank transaction data through configurable workflows. It supports multiple analysis methods including AI-powered categorization, data quality analysis, and comprehensive metadata collection for monitoring and debugging.

## Features

- **Modular Workflows**: Configurable data processing pipelines
- **AI Categorization**: AI-powered transaction categorization
- **Data Quality Analysis**: Comprehensive quality metrics and reporting
- **Metadata Collection**: Automatic execution tracking and performance monitoring
- **Containerized Development**: Podman-based development environment
- **Comprehensive Testing**: Full test coverage with pytest and coverage reporting
- **Code Quality**: Linting, formatting, and type checking with pylint, black, isort, and mypy

## Project Structure

```
balance/
├── src/analyzer/              # Main package
│   ├── pipeline/             # Core pipeline components
│   ├── workflows/            # Workflow definitions
│   └── pipeline_runner.py    # Main entry point
├── tests/                    # Comprehensive test suite
├── data/                     # Data directory
│   ├── extratos/            # Input bank extracts
│   ├── output/              # Processed results
│   └── training/            # Training data
├── context/                  # Configuration files
├── scripts/                  # Utility scripts
├── Dockerfile.dev           # Development container
├── Makefile                 # Local development targets
├── Makefile.podman          # Containerized development targets
├── pyproject.toml           # Poetry configuration
└── poetry.lock              # Locked dependencies
```

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry
- Podman (for containerized development)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/m-rossini/balance-category-pipeline.git
cd balance-category-pipeline
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with any required configuration
```

### Development Setup

#### Local Development
```bash
# Install dependencies
make install

# Run tests
make test

# Run with coverage
make coverage

# Lint code
make lint

# Format code
make format
```

#### Containerized Development
```bash
# Build development container
make -f Makefile.podman build-dev

# Run development container
make -f Makefile.podman run-dev

# Run tests in container
make -f Makefile.podman coverage

# Clean up
make -f Makefile.podman clean-dev
```

## Workflows

The system supports multiple named workflows, each defined in `src/analyzer/workflows/`.

### Available Workflows

- `bank_transaction_analysis` (default): Complete workflow with data loading, cleaning, feature derivation, and analysis
- `minimal_load`: Basic workflow that loads and saves bank data without processing
- `ai_categorization`: AI-powered categorization using external AI service
- `bank_extract_clean`: Data cleaning and preprocessing
- `derive_statement_features`: Feature engineering for transaction analysis

### Running Workflows

```bash
# Run default workflow
make transactions

# Run specific workflow
make transactions WORKFLOW=ai_categorization

# Run with custom log level
make transactions LOG_LEVEL=DEBUG

# Run with custom metadata directory
make transactions METADATA_DIR=/tmp/metadata
```

### AI Categorization

The AI categorization workflow uses an external AI service for intelligent transaction categorization.

**Configuration:**
```bash
export AI_SERVICE_URL="http://your-ai-service:5000/balance/"  # AI service endpoint
```

**Usage:**
```bash
# Run AI categorization
make ai-categorize

# Or directly
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow ai_categorization
```

## Testing

The project includes comprehensive testing with pytest:

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
PYTHONPATH=src poetry run pytest tests/test_ai_categorization_workflow.py

# Run tests in container
make -f Makefile.podman coverage
```

Coverage reports are generated in `htmlcov/` directory.

## Code Quality

```bash
# Lint code
make lint

# Format code
poetry run black src/analyzer
poetry run isort src/analyzer

# Type checking
poetry run mypy src/analyzer
```

## Metadata Collection

All pipeline runs automatically collect execution metadata:

- Pipeline execution details (start/end times, duration)
- Step-by-step performance metrics
- Data quality indices
- Input/output row counts
- Configuration parameters

Metadata is stored in `~/.metadata/pipelines/` by default or a custom directory specified by `METADATA_DIR`.

## Configuration

### Environment Variables

- `AI_SERVICE_URL`: AI service endpoint (default: http://perez:5000/balance/)

### Context Files

- `context/candidate_categories.json`: Category definitions for AI categorization
- `context/transaction_type_codes.json`: Transaction type mappings

## Development

### Adding New Workflows

1. Create `src/analyzer/workflows/your_workflow.py`
2. Define a `get_pipeline()` function returning a `DataPipeline` instance
3. Add import and registry entry in `pipeline_runner.py`

### Adding Tests

1. Create test files in `tests/` following the naming pattern `test_*.py`
2. Use pytest fixtures and assertions
3. Run `make coverage` to ensure coverage remains high

### Container Development

The development container includes all dependencies and tools:

```bash
# Attach to running container
podman exec -it my-python-app-dev-balance bash

# Run tests inside container
podman exec -it my-python-app-dev-balance pytest --cov=src tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass: `make test`
5. Format code: `make format`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
````
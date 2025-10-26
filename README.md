# Bank Transaction Analyzer

A data processing workflow system for analyzing bank transactions.

## Workflows

The system supports multiple named workflows, each defined in its own module under `src/analyzer/workflows/`.

### Available Workflows

- `bank_transaction_analysis` (default): Full workflow that loads bank data, cleans it, merges with training data, generates summaries, and saves results.
- `minimal_load`: Simple workflow that just loads bank data and saves it without processing.
- `ai_categorization`: AI-powered workflow that categorizes transactions using OpenAI's API with configurable parameters.

### AI Categorization Workflow

The `ai_categorization` workflow uses OpenAI's API to automatically categorize bank transactions. It's fully configurable via environment variables:

**Environment Variables:**
- `AI_MODEL`: OpenAI model to use (default: "gpt-3.5-turbo")
  - Options: "gpt-3.5-turbo", "gpt-4o-mini", "gpt-4", etc.
- `AI_BATCH_SIZE`: Transactions per API call (default: 25)
- `AI_TEMPERATURE`: AI creativity/randomness 0.0-1.0 (default: 0.1)
- `AI_MAX_TOKENS`: Maximum response tokens (default: 150)
- `OPENAI_API_KEY`: Your OpenAI API key (required)

**Usage Examples:**

```bash
# Default GPT-3.5-turbo (balanced performance/cost)
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow ai_categorization

# GPT-4o-mini (higher quality, more expensive)
AI_MODEL=gpt-4o-mini AI_BATCH_SIZE=20 AI_TEMPERATURE=0.0 \
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow ai_categorization

# High-throughput GPT-3.5-turbo (faster, lower quality)
AI_MODEL=gpt-3.5-turbo AI_BATCH_SIZE=50 AI_TEMPERATURE=0.2 \
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow ai_categorization

# Conservative GPT-4 (highest quality, slowest, most expensive)
AI_MODEL=gpt-4 AI_BATCH_SIZE=10 AI_TEMPERATURE=0.0 AI_MAX_TOKENS=300 \
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow ai_categorization
```

**Make Targets:**

For convenience, several make targets are available for common AI categorization configurations:

```bash
# Default balanced configuration
make ai-categorize

# Premium quality (GPT-4o-mini)
make ai-categorize-premium

# Fast processing (larger batches)
make ai-categorize-fast

# Conservative high-quality (GPT-4)
make ai-categorize-conservative

# Debug mode (shows AI prompts)
make ai-categorize-debug
```

**Output:** The workflow automatically generates output files named based on the model:
- `data/output/ai_categorized_gpt35turbo_bos.csv` (default)
- `data/output/ai_categorized_gpt4omini_bos.csv` (for GPT-4o-mini)
- `data/output/ai_categorized_gpt4_bos.csv` (for GPT-4)
- etc.

The AI uses context from `candidate_categories.json` and `transaction_type_codes.md` to provide accurate categorizations.

### Running Workflows

Use the workflow runner with the `--workflow` option:

```bash
# Run the default workflow (metadata collected to ~/.metadata/pipelines/)
make transactions

# Run a specific workflow
make transactions WORKFLOW=minimal_load

# Or directly with python (metadata mandatory)
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow bank_transaction_analysis --log-level INFO

# Store metadata in a custom directory
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner --workflow bank_transaction_analysis --metadata-dir /tmp/my_metadata
```

### Adding New Workflows

1. Create a new file in `src/analyzer/workflows/your_workflow_name.py`
2. Define a `get_pipeline()` function that returns a `DataPipeline` instance
3. Add the import and registry entry in `src/analyzer/pipeline_runner.py`

Example:

```python
from analyzer.pipeline.pipeline_commands import DataPipeline, AppendFilesCommand, SaveFileCommand

def get_pipeline():
    return DataPipeline([
        AppendFilesCommand(input_dir='data/extratos/bank_bos', file_glob='*.csv'),
        SaveFileCommand(output_path='data/output/result.csv')
    ])
```

Then add to the registry:
```python
from analyzer.workflows import your_workflow_name

WORKFLOW_REGISTRY = {
    'your_workflow_name': your_workflow_name.get_pipeline,
    # ... other workflows
}
```

## Metadata Collection

All pipeline runs automatically collect execution metadata for monitoring and analysis:

### What is Captured

- **Pipeline Execution**: Run ID, workflow name, start/end times, total duration
- **Step Details**: Each step captures:
  - Step name
  - Input/output row counts
  - Processing duration
  - Step parameters (if any)
- **Quality Index**: Placeholder for data quality metrics
- **Run History**: Permanent record with unique identification

### Metadata Storage

Metadata is automatically persisted to JSON files in `~/.metadata/pipelines/` by default.

**Custom Storage Location:**

```bash
# Store metadata in a specific directory
PYTHONPATH=src poetry run python -m analyzer.pipeline_runner \
  --workflow bank_transaction_analysis \
  --metadata-dir /var/log/pipeline_metadata
```

### Accessing Metadata

Metadata files are stored with the naming pattern: `{run_id}_{workflow_name}_{timestamp}.json`

Example metadata structure:

```json
{
  "run_id": "abc123def456",
  "pipeline_name": "bank_transaction_analysis",
  "start_time": "2025-10-26T10:30:45.123456",
  "end_time": "2025-10-26T10:35:12.654321",
  "duration_seconds": 267.531,
  "steps": [
    {
      "name": "AppendFilesCommand",
      "start_time": "2025-10-26T10:30:45.123456",
      "end_time": "2025-10-26T10:30:50.234567",
      "duration_seconds": 5.111,
      "input_rows": 0,
      "output_rows": 12345,
      "parameters": {}
    }
  ],
  "quality_index": null
}
```

### Using Metadata Programmatically

```python
from analyzer.pipeline.metadata import MetadataRepository
from pathlib import Path

# Load metadata from default location
repo = MetadataRepository()

# List all runs
runs = repo.list_runs()
print(f"Found {len(runs)} pipeline runs")

# Load specific metadata
metadata = repo.load(run_id="abc123def456")
print(f"Pipeline: {metadata.pipeline_name}")
print(f"Duration: {metadata.duration_seconds} seconds")
print(f"Steps executed: {len(metadata.steps)}")
```
````
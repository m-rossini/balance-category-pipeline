Pipeline failure metadata capture (2025-11-16)
===========================================

What changed
------------
- We added additional metadata fields to capture failures that happen during a pipeline run:
  - Step-level fields (included in each step's metadata):
    - `result_code` (int): command's return code; negative indicates failure.
    - `error` (dict | null): error details from the command if it failed (e.g. {"message": "..."}).
  - Pipeline-level fields (included in the pipeline metadata root):
    - `result_code` (int): the effective pipeline result (0 success, negative failure). On a step failure this is set to the negative return code of the failing step.
    - `error` (dict | null): pipeline-level error details (same shape as step error). When a step fails the pipeline `error` is set to the step's error.

Why it helps
------------
- Previously, exceptions (for example API errors) could be swallowed in the call, causing the pipeline to continue silently. Now any step error is captured in the metadata JSON; the pipeline halts and metadata is persisted so operations & debugging can inspect the cause easily.

Behavior notes
--------------
- When a step returns `return_code < 0` (failure):
  1. A `StepMetadata` entry is created with the `result_code` and `error` set.
  2. The pipeline `PipelineMetadata.result_code` and `PipelineMetadata.error` are set from the failing step.
  3. The pipeline stops and if a metadata `repository` is provided is saved immediately.
  4. The saved JSON will contain step-level `result_code` and `error`, and the pipeline-level `result_code` and `error`.

- When a step returns `return_code == 0` (success):
  - The step metadata contains `result_code: 0` and `error: null`.

What to look for in metadata JSON
---------------------------------
- The pipeline metadata JSON file will contain top-level keys like `pipeline_name`, `run_id`, `steps`, and `result_code` / `error`.
- Each step inside `steps` will include `result_code` and `error`:

Example (abridged):

```
{
  "pipeline_name": "bank_transaction_analysis",
  "run_id": "1c2c138b...",
  "result_code": -1,
  "error": {"message": "simulated failure"},
  "steps": [
    {
      "name": "AIRemoteCategorizationCommand",
      "result_code": -1,
      "error": {"message": "API connection failed"}
    }
  ]
}
```

How to inspect
--------------
- JSON files are saved under `~/.metadata/pipelines/` by default (or a custom `--metadata-dir` value). Example CLI usage:

  - Listing runs (shell): `ls ~/.metadata/pipelines` or `ls $METADATA_DIR`.
  - Open a run JSON: `jq '.' ~/.metadata/pipelines/<run_id>.json` or `less <path>`.

Future ideas
------------
- Add structured error fields: `exception_type`, `trace`, `api_error_count` to support richer diagnostics.
- Add a helper CLI to query runs by `result_code` or to extract failing steps quickly.

Commit and test notes
---------------------
- Code changes were implemented in:
  - `src/analyzer/pipeline/metadata.py` — add `result_code` & `error` fields for step and pipeline
  - `src/analyzer/pipeline/pipeline_commands.py` — record step and pipeline errors and save metadata on failure
  - `tests/` — new tests to cover that pipeline failure metadata is saved
- Full test suite run via `make test` passed.


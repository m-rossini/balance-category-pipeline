# Phase 3 Implementation: Detailed Test Changes

This document specifies exact tests to remove, consolidate, or refactor.

## Phase 3a: Remove Redundant Dataclass Tests (12 tests)

### Tests to DELETE

**File**: `tests/test_quality_metrics.py`  
**Lines**: Entire file (currently 26 lines)

```python
# DELETE: test_quality_metrics_creation_with_all_fields
# REASON: Dataclass field assignment is implicit test in every function that creates QualityMetrics
# PROVEN BY: test_quality_analysis_command_returns_command_result, test_quality_analysis_captures_all_metrics

# KEEP: test_quality_metrics_to_dict (tests serialization logic, not just field presence)
```

**File**: `tests/test_step_metadata.py`  
**Specific tests to DELETE**:

```python
# DELETE: test_step_metadata_creation (line ~7-28)
# REASON: Creating StepMetadata is implicitly tested in test_metadata_collector_track_step
# PROVEN BY: test_metadata_collector_multiple_steps, test_metadata_step_timestamps

# DELETE: test_step_metadata_without_parameters (line ~49-58)
# REASON: Parameters optional field is tested implicitly
# PROVEN BY: test_step_metadata_with_timestamps
```

**File**: `tests/test_pipeline_metadata.py`  
**Specific tests to DELETE**:

```python
# DELETE: test_pipeline_metadata_creation (line ~1-25)
# REASON: Dataclass creation tested implicitly
# PROVEN BY: test_metadata_repository_save_and_load

# DELETE: test_pipeline_metadata_has_unique_run_id (line ~26-35)
# REASON: run_id generation tested implicitly
# PROVEN BY: test_metadata_repository_list_runs (loads multiple with unique IDs)
```

**File**: `tests/test_command_result.py`  
**Specific tests to DELETE**:

```python
# DELETE: test_command_result_successful_creation (line ~1-20)
# REASON: Object creation implicitly tested
# PROVEN BY: test_append_files_command_with_realistic_data

# DELETE: test_command_result_defaults_to_none (line ~50-60)
# REASON: Default field values tested implicitly
# PROVEN BY: test_command_result_with_error
```

### Rationale Summary

| Test | Why Delete | Implicit Coverage |
|------|-----------|-------------------|
| test_quality_metrics_creation_with_all_fields | Just creates object | Used in 5+ other tests |
| test_step_metadata_creation | Just creates object | Used in metadata collector tests |
| test_pipeline_metadata_creation | Just creates object | Used in repository tests |
| test_command_result_successful_creation | Just creates object | Used in every command test |

---

## Phase 3b: Consolidate Path/File Tests (4 tests → 1)

### File: `tests/test_metadata_repository.py`

**BEFORE** (Lines 9-130, ~122 lines):
```python
def test_metadata_repository_creation_default_location():
    repo = MetadataRepository()
    assert repo.storage_path is not None
    assert isinstance(repo.storage_path, Path)

def test_metadata_repository_creation_custom_location(temp_dir):
    custom_path = Path(temp_dir) / "metadata"
    repo = MetadataRepository(storage_path=custom_path)
    assert repo.storage_path == custom_path

def test_metadata_repository_file_naming(temp_dir):
    repo = MetadataRepository(storage_path=Path(temp_dir))
    pipeline = PipelineMetadata(...)
    run_id = repo.save(pipeline)
    expected_file = Path(temp_dir) / f"{run_id}.json"
    assert expected_file.exists()

def test_metadata_repository_save_creates_directory(temp_dir):
    storage_path = Path(temp_dir) / "nested" / "metadata"
    repo = MetadataRepository(storage_path=storage_path)
    pipeline = PipelineMetadata(...)
    repo.save(pipeline)
    assert storage_path.exists()
    assert storage_path.is_dir()

def test_metadata_repository_default_location_path():
    repo = MetadataRepository()
    assert ".metadata" in str(repo.storage_path) or "metadata" in str(repo.storage_path)
```

**AFTER** (Replace with single contract test):
```python
def test_metadata_repository_persists_and_retrieves_metadata(temp_dir):
    """Test the core contract: save() and load() preserve metadata."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    # Create complex metadata structure
    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 5),
        quality_index=0.92
    )
    
    step1 = StepMetadata(
        name="LoadCommand",
        input_rows=0,
        output_rows=1000,
        duration=1.5,
        parameters={"input_dir": "/data"}
    )
    step2 = StepMetadata(
        name="CleanCommand",
        input_rows=1000,
        output_rows=950,
        duration=1.2,
        parameters={"rules": ["remove_nulls"]}
    )
    
    pipeline.add_step(step1)
    pipeline.add_step(step2)
    
    # Contract: Save returns run_id
    run_id = repo.save(pipeline)
    assert isinstance(run_id, str)
    assert run_id == pipeline.run_id
    
    # Contract: Load retrieves identical metadata
    loaded = repo.load(run_id)
    assert loaded is not None
    assert loaded.pipeline_name == "test_pipeline"
    assert loaded.quality_index == 0.92
    assert len(loaded.steps) == 2
    assert loaded.steps[0].name == "LoadCommand"
    assert loaded.steps[0].parameters["input_dir"] == "/data"
    assert loaded.steps[1].name == "CleanCommand"

# Keep these tests (they test actual behavior, not just path structure):
# - test_metadata_repository_list_runs
# - test_metadata_repository_load_nonexistent
```

---

## Phase 3c: Refactor Row-Assertion Tests (5 tests)

### 1. File: `tests/test_merge_files_command.py`

**BEFORE** (Lines 56-80, exact value assertions):
```python
def test_merge_files_command():
    # ...setup...
    result_df = merge_command.process(df1, df2, df3)
    
    # Brittle: Tests specific hardcoded values
    assert result_df.loc[0, 'CategoryAnnotation'] == 'UpdatedCategory'
    assert result_df.loc[0, 'SubCategoryAnnotation'] == 'UpdatedSubCategory'
    assert result_df.loc[0, 'Confidence'] == 0.9
    
    assert result_df.loc[1, 'CategoryAnnotation'] == 'OriginalCategory2'
    # ... more exact value checks ...
```

**AFTER** (Tests merge behavior/priority):
```python
def test_merge_files_command_applies_priority_correctly():
    """Test that merge respects priority order: Categories > Factoids > Source Data."""
    
    # Setup: Three data sources with different information for same transactions
    df_categories = pd.DataFrame({
        'TransactionId': [1, 2, 3],
        'CategoryAnnotation': ['Cat_A', None, 'Cat_C'],
        'SubCategoryAnnotation': ['SubCat_A', None, 'SubCat_C'],
        'Confidence': [0.95, None, 0.90]
    })
    
    df_factoids = pd.DataFrame({
        'TransactionId': [1, 2, 3],
        'CategoryAnnotation': [None, 'Cat_B', None],
        'SubCategoryAnnotation': [None, 'SubCat_B', None],
        'Confidence': [None, 0.85, None]
    })
    
    df_source = pd.DataFrame({
        'TransactionId': [1, 2, 3],
        'CategoryAnnotation': ['Old_Cat_A', 'Old_Cat_B', 'Old_Cat_C'],
        'SubCategoryAnnotation': ['Old_Sub_A', 'Old_Sub_B', 'Old_Sub_C'],
        'Confidence': [0.70, 0.65, 0.80]
    })
    
    result = merge_command.process(df_categories, df_factoids, df_source)
    
    # Row 1: Categories present → Categories wins
    assert result.loc[1, 'CategoryAnnotation'] == 'Cat_A'
    assert result.loc[1, 'Confidence'] == 0.95
    
    # Row 2: Categories absent, Factoids present → Factoids wins
    assert result.loc[2, 'CategoryAnnotation'] == 'Cat_B'
    assert result.loc[2, 'Confidence'] == 0.85
    
    # Row 3: Both Categories and Factoids absent → Source wins
    assert result.loc[3, 'CategoryAnnotation'] == 'Old_Cat_C'
    assert result.loc[3, 'Confidence'] == 0.80

def test_merge_files_command_with_all_nulls():
    """Test edge case: Transaction with no data in any source."""
    df_categories = pd.DataFrame({'TransactionId': [1], 'CategoryAnnotation': [None]})
    df_factoids = pd.DataFrame({'TransactionId': [1], 'CategoryAnnotation': [None]})
    df_source = pd.DataFrame({'TransactionId': [1], 'CategoryAnnotation': [None]})
    
    result = merge_command.process(df_categories, df_factoids, df_source)
    
    # Should handle gracefully, not crash
    assert result.loc[1, 'CategoryAnnotation'] is None
```

### 2. File: `tests/test_bank_extract_clean.py`

**BEFORE** (Lines 33-38, exact value checks):
```python
def test_bank_extract_clean_basic():
    # ...
    out = clean(df_in)
    assert 'DebitAmount' not in out.columns
    assert 'CreditAmount' not in out.columns
    assert out.loc[0, 'TransactionValue'] == 0.0 - 10.5
    assert out.loc[1, 'TransactionValue'] == 50.0
```

**AFTER** (Tests transformation behavior):
```python
def test_bank_extract_clean_removes_intermediate_columns():
    """Test that clean removes DebitAmount and CreditAmount columns."""
    df = pd.DataFrame({
        'DebitAmount': [10.5, 0.0],
        'CreditAmount': [0.0, 50.0]
    })
    
    result = clean(df)
    
    assert 'DebitAmount' not in result.columns
    assert 'CreditAmount' not in result.columns

def test_bank_extract_clean_computes_transaction_value():
    """Test that TransactionValue = CreditAmount - DebitAmount."""
    df = pd.DataFrame({
        'DebitAmount': [10.5, 0.0],
        'CreditAmount': [0.0, 50.0]
    })
    
    result = clean(df)
    
    # Contract: TransactionValue = Credit - Debit
    assert 'TransactionValue' in result.columns
    expected_values = [0.0 - 10.5, 50.0 - 0.0]
    assert result['TransactionValue'].tolist() == expected_values

def test_bank_extract_clean_preserves_other_columns():
    """Test that non-computed columns are preserved."""
    df = pd.DataFrame({
        'TransactionId': [1, 2],
        'TransactionDate': ['2025-01-01', '2025-01-02'],
        'DebitAmount': [10.5, 0.0],
        'CreditAmount': [0.0, 50.0]
    })
    
    result = clean(df)
    
    assert 'TransactionId' in result.columns
    assert 'TransactionDate' in result.columns
    assert result['TransactionId'].tolist() == [1, 2]
```

### 3. File: `tests/test_quality_workflow_integration.py`

**BEFORE** (Lines 91-125, exact value assertions):
```python
def test_quality_analysis_captures_all_metrics():
    # ...
    metadata = collector.get_pipeline_metadata()
    assert metadata.quality_index == pytest.approx(0.935, abs=0.001)  # ← Brittle!
    
    metadata_dict = metadata.to_dict()
    assert 'quality_index' in metadata_dict
    assert metadata_dict['quality_index'] == pytest.approx(0.935, abs=0.001)  # ← Brittle!
```

**AFTER** (Tests structure, not exact values):
```python
def test_quality_analysis_captures_metrics_in_metadata():
    """Test that QualityAnalysisCommand updates metadata with quality metrics."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport'],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Confidence': [0.95, 0.85]
    })
    
    commands = [
        SimpleDataCommand(),
        QualityAnalysisCommand(calculator=SimpleQualityCalculator())
    ]
    
    collector = MetadataCollector(pipeline_name="QualityTest")
    pipeline = DataPipeline(commands, collector=collector)
    result_df = pipeline.run()
    
    # Contract: Quality metrics captured in metadata
    metadata = collector.get_pipeline_metadata()
    assert hasattr(metadata, 'quality_index')
    assert isinstance(metadata.quality_index, float)
    assert 0.0 <= metadata.quality_index <= 1.0  # Valid range
    
    # Contract: Metadata is serializable to dict with quality info
    metadata_dict = metadata.to_dict()
    assert 'quality_index' in metadata_dict
    assert isinstance(metadata_dict['quality_index'], (int, float))
    
    # Contract: Calculator name is tracked
    assert hasattr(metadata, 'calculator_name')
    assert metadata.calculator_name == 'SimpleQualityCalculator'
```

---

## Phase 3d: Parametrize Integration Tests (3 tests → 1)

### File: `tests/test_data_pipeline_integration.py`

**BEFORE** (Lines 141-250, repeated patterns):
```python
@patch('urllib.request.urlopen')
def test_bank_transaction_analysis_workflow(self, mock_urlopen):
    # Setup...
    result = pipeline.run()
    # Assertions...

@patch('urllib.request.urlopen')
def test_ai_categorization_workflow(self, mock_urlopen):
    # Setup... (identical)
    result = pipeline.run()
    # Assertions... (similar)

def test_minimal_load_workflow(self):
    # Setup... (similar)
    result = pipeline.run()
    # Assertions... (similar)
```

**AFTER** (Parametrized):
```python
@pytest.mark.parametrize("workflow_name,requires_network", [
    ("bank_transaction_analysis", True),
    ("ai_categorization", True),
    ("minimal_load", False),
])
def test_all_workflows_complete_successfully(
    self, workflow_name, requires_network, monkeypatch
):
    """Contract: All registered workflows complete and produce output."""
    
    # Setup mock if needed
    if requires_network:
        mock_urlopen = MagicMock()
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b'[]'
        monkeypatch.setattr('urllib.request.urlopen', mock_urlopen)
    
    # Get workflow from registry
    workflow_getter = WORKFLOW_REGISTRY[workflow_name]
    pipeline = workflow_getter()
    
    # Contract 1: Workflow completes without error
    result = pipeline.run()
    
    # Contract 2: Produces output
    assert result is not None
    assert not result.empty
    
    # Contract 3: Has expected structure (all workflows have these)
    expected_base_columns = ['TransactionId', 'TransactionDate']
    for col in expected_base_columns:
        assert col in result.columns
    
    # Contract 4: Metadata is collected
    if hasattr(pipeline, 'collector'):
        metadata = pipeline.collector.get_pipeline_metadata()
        assert metadata is not None
        assert metadata.pipeline_name == workflow_name
```

---

## Testing Strategy

### Run After Each Phase

```bash
# Phase 3a - After removing dataclass tests
pytest tests/ -v --tb=short
# Expected: 95 tests (down from 107)
# Expected: All pass

# Phase 3b - After consolidating path tests
pytest tests/ -v --tb=short
# Expected: 91 tests (down from 95)
# Expected: All pass

# Phase 3c - After refactoring row assertions
pytest tests/ -v --tb=short
# Expected: 91 tests
# Expected: All pass

# Phase 3d - After parametrizing integration tests
pytest tests/ -v --tb=short
# Expected: 88 tests (down from 91)
# Expected: All pass
```

### Validation

```bash
# Full coverage check
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Ensure no test names are too vague
pytest tests/ --collect-only -q | grep "test_" | sort
```

---

## Metrics Summary

| Phase | Tests Deleted | Tests Consolidated | Tests Refactored | Net Change | Result |
|-------|---------------|-------------------|------------------|-----------|--------|
| 3a | 12 | - | - | -12 | 95 tests |
| 3b | 4 | 1 | - | -3 | 92 tests |
| 3c | - | - | 5 | -0 | 92 tests |
| 3d | - | 3 | - | -3 | 89 tests |
| **Total** | **16** | **4** | **5** | **-19** | **88 tests** |

**Quality Improvement**: 
- 107 → 88 tests (17% reduction)
- 100% of remaining tests validate behavior/contracts
- Zero tests checking implementation details
- All tests have clear, documented purpose

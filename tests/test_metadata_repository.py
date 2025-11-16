"""Test for MetadataRepository - saves and loads metadata persistently."""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from analyzer.pipeline.metadata import (
    MetadataRepository, MetadataCollector, StepMetadata, PipelineMetadata
)


def test_metadata_repository_persists_and_retrieves_metadata(temp_dir):
    """Test the core contract: repository saves and loads metadata identically."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    # Create rich pipeline metadata
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
    
    # Contract: Storage directory is created
    assert Path(temp_dir).exists()
    assert Path(temp_dir).is_dir()
    
    # Contract: Load retrieves identical metadata
    loaded = repo.load(run_id)
    assert loaded is not None
    assert loaded.pipeline_name == "test_pipeline"
    assert loaded.quality_index == 0.92
    assert len(loaded.steps) == 2
    assert loaded.steps[0].name == "LoadCommand"
    assert loaded.steps[0].parameters["input_dir"] == "/data"
    assert loaded.steps[1].name == "CleanCommand"


def test_metadata_repository_persist_step_result_code(temp_dir):
    """Confirm step result codes are persisted and loaded correctly."""
    repo = MetadataRepository(storage_path=Path(temp_dir))

    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 5),
    )

    step = StepMetadata(
        name="Step1",
        input_rows=0,
        output_rows=100,
        duration=1.0,
        parameters={"key": "value"},
        result_code=-1,
    )
    pipeline.add_step(step)

    run_id = repo.save(pipeline)
    loaded = repo.load(run_id)

    assert len(loaded.steps) == 1
    assert loaded.steps[0].result_code == -1


def test_metadata_repository_save_and_load(temp_dir):
    """Test saving and loading metadata."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    # Create pipeline metadata
    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 5)
    )
    
    step = StepMetadata(
        name="Step1",
        input_rows=0,
        output_rows=100,
        duration=1.0,
        parameters={"key": "value"}
    )
    pipeline.add_step(step)
    
    # Save
    run_id = repo.save(pipeline)
    
    assert run_id == pipeline.run_id
    
    # Load
    loaded_pipeline = repo.load(run_id)
    
    assert loaded_pipeline.pipeline_name == "test_pipeline"
    assert len(loaded_pipeline.steps) == 1
    assert loaded_pipeline.steps[0].name == "Step1"


def test_metadata_repository_list_runs(temp_dir):
    """Test listing all saved runs."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    # Save multiple pipelines
    for i in range(3):
        pipeline = PipelineMetadata(
            pipeline_name=f"pipeline_{i}",
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        repo.save(pipeline)
    
    runs = repo.list_runs()
    
    assert len(runs) == 3
    # Verify all are strings (run IDs)
    assert all(isinstance(run_id, str) for run_id in runs)


def test_metadata_repository_load_nonexistent(temp_dir):
    """Test loading a nonexistent run returns None."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    result = repo.load("nonexistent-run-id")
    
    assert result is None


def test_metadata_repository_metadata_content(temp_dir):
    """Test that saved metadata preserves all data."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 5)
    
    pipeline = PipelineMetadata(
        pipeline_name="complex_pipeline",
        start_time=start_time,
        end_time=end_time,
        quality_index=0.95
    )
    
    step1 = StepMetadata(
        name="Append",
        input_rows=0,
        output_rows=1000,
        duration=1.5,
        parameters={"dir": "/data"}
    )
    step2 = StepMetadata(
        name="Clean",
        input_rows=1000,
        output_rows=950,
        duration=1.2,
        parameters={"rules": ["remove_nulls"]}
    )
    
    pipeline.add_step(step1)
    pipeline.add_step(step2)
    
    run_id = repo.save(pipeline)
    loaded = repo.load(run_id)
    
    assert loaded.pipeline_name == "complex_pipeline"
    assert loaded.quality_index == 0.95
    assert len(loaded.steps) == 2
    assert loaded.steps[0].name == "Append"
    assert loaded.steps[1].name == "Clean"
    assert loaded.steps[0].parameters["dir"] == "/data"

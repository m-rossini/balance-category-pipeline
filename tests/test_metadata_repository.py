"""Test for MetadataRepository - saves and loads metadata persistently."""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from analyzer.pipeline.metadata import (
    MetadataRepository, MetadataCollector, StepMetadata, PipelineMetadata
)


def test_metadata_repository_creation_default_location():
    """Test that MetadataRepository can be created with default location."""
    repo = MetadataRepository()
    
    assert repo.storage_path is not None
    assert isinstance(repo.storage_path, Path)


def test_metadata_repository_creation_custom_location(temp_dir):
    """Test that MetadataRepository can be created with custom location."""
    custom_path = Path(temp_dir) / "metadata"
    repo = MetadataRepository(storage_path=custom_path)
    
    assert repo.storage_path == custom_path


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


def test_metadata_repository_save_creates_directory(temp_dir):
    """Test that saving metadata creates the storage directory if it doesn't exist."""
    storage_path = Path(temp_dir) / "nested" / "metadata"
    repo = MetadataRepository(storage_path=storage_path)
    
    pipeline = PipelineMetadata(
        pipeline_name="test",
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    
    repo.save(pipeline)
    
    assert storage_path.exists()
    assert storage_path.is_dir()


def test_metadata_repository_file_naming(temp_dir):
    """Test that saved files follow the run_id pattern."""
    repo = MetadataRepository(storage_path=Path(temp_dir))
    
    pipeline = PipelineMetadata(
        pipeline_name="test",
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    
    run_id = repo.save(pipeline)
    
    # Check that a file with the run_id exists
    expected_file = Path(temp_dir) / f"{run_id}.json"
    assert expected_file.exists()


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


def test_metadata_repository_default_location_path():
    """Test that the default storage path is reasonable."""
    repo = MetadataRepository()
    
    # Default should be in a .metadata directory
    assert ".metadata" in str(repo.storage_path) or "metadata" in str(repo.storage_path)


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

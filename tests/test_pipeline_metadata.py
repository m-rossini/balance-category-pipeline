"""Test for PipelineMetadata - captures metadata of entire pipeline execution."""
import pytest
from datetime import datetime
from analyzer.pipeline.metadata import PipelineMetadata, StepMetadata


def test_pipeline_metadata_creation():
    """Test that PipelineMetadata can be created with basic information."""
    pipeline_name = "bank_transaction_analysis"
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 5)
    
    metadata = PipelineMetadata(
        pipeline_name=pipeline_name,
        start_time=start_time,
        end_time=end_time
    )
    
    assert metadata.pipeline_name == pipeline_name
    assert metadata.start_time == start_time
    assert metadata.end_time == end_time
    assert metadata.run_id is not None  # Should have a unique ID
    assert len(metadata.steps) == 0  # Initially empty


def test_pipeline_metadata_has_unique_run_id():
    """Test that each PipelineMetadata instance has a unique run_id."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 1)
    
    metadata1 = PipelineMetadata(
        pipeline_name="workflow1",
        start_time=start_time,
        end_time=end_time
    )
    
    metadata2 = PipelineMetadata(
        pipeline_name="workflow2",
        start_time=start_time,
        end_time=end_time
    )
    
    assert metadata1.run_id != metadata2.run_id


def test_pipeline_metadata_calculates_duration():
    """Test that PipelineMetadata calculates total duration."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 5, 500000)  # 5.5 seconds
    
    metadata = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=start_time,
        end_time=end_time
    )
    
    assert metadata.total_duration == pytest.approx(5.5, abs=0.01)


def test_pipeline_metadata_add_step():
    """Test adding step metadata to pipeline metadata."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 5)
    
    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=start_time,
        end_time=end_time
    )
    
    step = StepMetadata(
        name="AppendFilesCommand",
        input_rows=0,
        output_rows=1000,
        duration=1.0,
        parameters={"input_dir": "/data"}
    )
    
    pipeline.add_step(step)
    
    assert len(pipeline.steps) == 1
    assert pipeline.steps[0] == step


def test_pipeline_metadata_input_output_rows():
    """Test that PipelineMetadata tracks total input and output rows."""
    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 5)
    )
    
    step1 = StepMetadata("Step1", input_rows=0, output_rows=1000, duration=1.0, parameters={})
    step2 = StepMetadata("Step2", input_rows=1000, output_rows=950, duration=1.0, parameters={})
    step3 = StepMetadata("Step3", input_rows=950, output_rows=950, duration=1.0, parameters={})
    
    pipeline.add_step(step1)
    pipeline.add_step(step2)
    pipeline.add_step(step3)
    
    # Total input should be from first step (0), total output from last step (950)
    assert pipeline.input_rows == 0 or pipeline.input_rows is None
    assert pipeline.output_rows == 950


def test_pipeline_metadata_quality_index():
    """Test that PipelineMetadata has a placeholder for quality_index."""
    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 5),
        quality_index=None  # Placeholder for now
    )
    
    assert hasattr(pipeline, 'quality_index')


def test_pipeline_metadata_to_dict():
    """Test that PipelineMetadata can be serialized to dict."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 5)
    
    pipeline = PipelineMetadata(
        pipeline_name="test_pipeline",
        start_time=start_time,
        end_time=end_time
    )
    
    step = StepMetadata("Step1", input_rows=0, output_rows=100, duration=1.0, parameters={})
    pipeline.add_step(step)
    
    metadata_dict = pipeline.to_dict()
    
    assert isinstance(metadata_dict, dict)
    assert metadata_dict["pipeline_name"] == "test_pipeline"
    assert "run_id" in metadata_dict
    assert metadata_dict["total_duration"] == pytest.approx(5.0, abs=0.01)
    assert len(metadata_dict["steps"]) == 1
    assert metadata_dict["steps"][0]["name"] == "Step1"

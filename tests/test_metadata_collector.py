"""Test for MetadataCollector - collects metadata during pipeline execution."""
import pytest
import time
from datetime import datetime
from analyzer.pipeline.metadata import MetadataCollector, StepMetadata, PipelineMetadata


def test_metadata_collector_creation():
    """Test that MetadataCollector can be created."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    
    assert collector.pipeline_name == "test_pipeline"
    assert collector.pipeline_metadata is None  # Not started yet


def test_metadata_collector_start_pipeline():
    """Test starting pipeline metadata collection."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    
    collector.start_pipeline()
    
    assert collector.pipeline_metadata is not None
    assert collector.pipeline_metadata.pipeline_name == "test_pipeline"
    assert collector.pipeline_metadata.start_time is not None


def test_metadata_collector_end_pipeline():
    """Test ending pipeline metadata collection."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    collector.start_pipeline()
    
    time.sleep(0.01)  # Small delay to ensure some time passes
    collector.end_pipeline()
    
    assert collector.pipeline_metadata.end_time is not None
    assert collector.pipeline_metadata.total_duration > 0


def test_metadata_collector_track_step():
    """Test tracking a step's metadata."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    collector.start_pipeline()
    
    step = StepMetadata(
        name="AppendFilesCommand",
        input_rows=0,
        output_rows=1000,
        duration=1.5,
        parameters={"input_dir": "/data"}
    )
    
    collector.track_step(step)
    
    assert len(collector.pipeline_metadata.steps) == 1
    assert collector.pipeline_metadata.steps[0].name == "AppendFilesCommand"


def test_metadata_collector_multiple_steps():
    """Test tracking multiple steps."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    collector.start_pipeline()
    
    step1 = StepMetadata("Step1", input_rows=0, output_rows=100, duration=0.5, parameters={})
    step2 = StepMetadata("Step2", input_rows=100, output_rows=90, duration=0.3, parameters={})
    step3 = StepMetadata("Step3", input_rows=90, output_rows=90, duration=0.2, parameters={})
    
    collector.track_step(step1)
    collector.track_step(step2)
    collector.track_step(step3)
    
    assert len(collector.pipeline_metadata.steps) == 3
    assert collector.pipeline_metadata.steps[1].name == "Step2"


def test_metadata_collector_get_pipeline_metadata():
    """Test retrieving the collected pipeline metadata."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    collector.start_pipeline()
    
    step = StepMetadata("Step1", input_rows=0, output_rows=100, duration=1.0, parameters={})
    collector.track_step(step)
    
    collector.end_pipeline()
    
    metadata = collector.get_pipeline_metadata()
    
    assert isinstance(metadata, PipelineMetadata)
    assert metadata.pipeline_name == "test_pipeline"
    assert len(metadata.steps) == 1
    assert metadata.output_rows == 100


def test_metadata_collector_context_manager():
    """Test using MetadataCollector as a context manager."""
    with MetadataCollector(pipeline_name="context_pipeline") as collector:
        assert collector.pipeline_metadata is not None
        
        step = StepMetadata("Step1", input_rows=0, output_rows=50, duration=0.5, parameters={})
        collector.track_step(step)
    
    # After exiting context, metadata should be finalized
    metadata = collector.get_pipeline_metadata()
    assert metadata.end_time is not None
    assert metadata.total_duration > 0


def test_metadata_collector_without_steps():
    """Test metadata collection for pipeline with no steps."""
    collector = MetadataCollector(pipeline_name="empty_pipeline")
    collector.start_pipeline()
    time.sleep(0.01)
    collector.end_pipeline()
    
    metadata = collector.get_pipeline_metadata()
    
    assert len(metadata.steps) == 0
    assert metadata.total_duration > 0

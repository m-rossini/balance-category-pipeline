"""Test MetadataCollector with optional PipelineMetadata parameter."""
import pytest
from datetime import datetime
from analyzer.pipeline.metadata import MetadataCollector, PipelineMetadata, StepMetadata


def test_metadata_collector_accepts_pipeline_metadata():
    """Test that MetadataCollector can accept an optional PipelineMetadata instance."""
    existing_metadata = PipelineMetadata(
        pipeline_name="existing_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 1)
    )
    
    collector = MetadataCollector(
        pipeline_name="my_pipeline",
        pipeline_metadata=existing_metadata
    )
    
    assert collector.pipeline_metadata == existing_metadata
    assert collector.pipeline_metadata.pipeline_name == "existing_pipeline"


def test_metadata_collector_creates_metadata_if_not_provided():
    """Test that MetadataCollector creates its own metadata if none provided."""
    collector = MetadataCollector(pipeline_name="auto_pipeline")
    
    assert collector.pipeline_metadata is None  # Not created until start_pipeline() is called
    
    collector.start_pipeline()
    
    assert collector.pipeline_metadata is not None
    assert collector.pipeline_metadata.pipeline_name == "auto_pipeline"


def test_metadata_collector_uses_provided_metadata():
    """Test that provided metadata is used when starting pipeline."""
    existing_metadata = PipelineMetadata(
        pipeline_name="reused_pipeline",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 1)
    )
    original_run_id = existing_metadata.run_id
    
    collector = MetadataCollector(
        pipeline_name="my_pipeline",
        pipeline_metadata=existing_metadata
    )
    
    collector.start_pipeline()
    
    # Should use the provided metadata with its original run_id
    metadata = collector.get_pipeline_metadata()
    assert metadata.run_id == original_run_id
    assert metadata.pipeline_name == "reused_pipeline"


def test_metadata_collector_adds_steps_to_provided_metadata():
    """Test that steps added to collector are added to provided metadata."""
    existing_metadata = PipelineMetadata(
        pipeline_name="pipeline_with_steps",
        start_time=datetime(2025, 10, 26, 10, 0, 0),
        end_time=datetime(2025, 10, 26, 10, 0, 5)
    )
    
    collector = MetadataCollector(
        pipeline_name="unused",
        pipeline_metadata=existing_metadata
    )
    
    step1 = StepMetadata("Step1", 0, 100, 1.0, {})
    step2 = StepMetadata("Step2", 100, 95, 1.0, {})
    
    collector.track_step(step1)
    collector.track_step(step2)
    
    metadata = collector.get_pipeline_metadata()
    assert len(metadata.steps) == 2
    assert metadata.steps[0].name == "Step1"
    assert metadata.steps[1].name == "Step2"

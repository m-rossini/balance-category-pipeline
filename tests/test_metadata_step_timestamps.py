"""Test that step metadata captures start_time and end_time."""
import pytest
import pandas as pd
from datetime import datetime
from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand
from analyzer.pipeline.command_result import CommandResult
from analyzer.pipeline.metadata import MetadataCollector


class SimpleCommand(PipelineCommand):
    """Simple test command."""
    
    def process(self, df: pd.DataFrame) -> CommandResult:
        """Return input DataFrame unchanged."""
        return CommandResult(return_code=0, data=df)


def test_step_metadata_has_start_time():
    """Test that StepMetadata captures start_time."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline([SimpleCommand()], collector=collector)
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # Verify start_time is populated
    assert len(metadata.steps) == 1
    assert metadata.steps[0].start_time is not None
    assert isinstance(metadata.steps[0].start_time, datetime)


def test_step_metadata_has_end_time():
    """Test that StepMetadata captures end_time."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline([SimpleCommand()], collector=collector)
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # Verify end_time is populated
    assert len(metadata.steps) == 1
    assert metadata.steps[0].end_time is not None
    assert isinstance(metadata.steps[0].end_time, datetime)


def test_step_metadata_times_are_ordered():
    """Test that start_time is before end_time."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline([SimpleCommand()], collector=collector)
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # Verify ordering
    step = metadata.steps[0]
    assert step.start_time < step.end_time


def test_multiple_steps_have_timestamps():
    """Test that all steps in a multi-step pipeline capture timestamps."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline(
        [SimpleCommand(), SimpleCommand(), SimpleCommand()],
        collector=collector
    )
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # Verify all steps have timestamps
    assert len(metadata.steps) == 3
    for i, step in enumerate(metadata.steps):
        assert step.start_time is not None, f"Step {i} missing start_time"
        assert step.end_time is not None, f"Step {i} missing end_time"
        assert step.start_time < step.end_time, f"Step {i} times not ordered"

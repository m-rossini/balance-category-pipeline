"""Integration test - DataPipeline with metadata collection."""
import pytest
import tempfile
from pathlib import Path
import pandas as pd
from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand, CommandResult
from analyzer.pipeline.metadata import MetadataCollector, MetadataRepository


class SimpleCommand(PipelineCommand):
    """Simple test command that creates a DataFrame."""
    def process(self, df: pd.DataFrame, context=None) -> CommandResult:
        if df is None or df.empty:
            df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        return CommandResult(return_code=0, data=df)


def test_data_pipeline_accepts_metadata_collector():
    """Test that DataPipeline can accept a MetadataCollector as optional parameter."""
    commands = [SimpleCommand()]
    collector = MetadataCollector(pipeline_name="test_pipeline")
    
    # DataPipeline should accept collector as optional parameter
    pipeline = DataPipeline(commands, collector=collector)
    
    assert pipeline.collector == collector


def test_data_pipeline_with_no_collector():
    """Test that DataPipeline creates its own collector even when none provided."""
    commands = [SimpleCommand()]
    
    # DataPipeline creates its own collector
    pipeline = DataPipeline(commands)
    
    assert pipeline.collector is not None
    # Default name when created internally
    assert pipeline.collector.pipeline_name == "DataPipeline"


def test_data_pipeline_run_collects_metadata():
    """Test that DataPipeline.run() automatically collects metadata for each step."""
    commands = [SimpleCommand(), SimpleCommand()]
    collector = MetadataCollector(pipeline_name="metadata_tracking_pipeline")
    
    pipeline = DataPipeline(commands, collector=collector)
    
    # Run pipeline - should automatically collect metadata
    result_df = pipeline.run()
    
    # Verify metadata was collected
    metadata = collector.get_pipeline_metadata()
    
    assert metadata is not None
    assert len(metadata.steps) == 2
    assert metadata.steps[0].name == "SimpleCommand"
    assert metadata.steps[1].name == "SimpleCommand"
    assert all(step.duration > 0 for step in metadata.steps)
    assert result_df is not None
    assert len(result_df) == 3  # SimpleCommand creates 3 rows


def test_data_pipeline_saves_metadata_automatically():
    """Test that DataPipeline automatically saves metadata when repository provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        repo = MetadataRepository(storage_path=storage_path)
        collector = MetadataCollector(pipeline_name="auto_save_pipeline")
        
        commands = [SimpleCommand()]
        pipeline = DataPipeline(commands, collector=collector)
        
        # Pass repository to run() - should automatically save
        result_df = pipeline.run(repository=repo)
        
        # Verify metadata was saved
        runs = repo.list_runs()
        
        assert len(runs) == 1
        
        # Load and verify
        loaded_metadata = repo.load(runs[0])
        
        assert loaded_metadata is not None
        assert loaded_metadata.pipeline_name == "auto_save_pipeline"
        assert len(loaded_metadata.steps) == 1
        assert loaded_metadata.output_rows == 3


    def test_data_pipeline_saves_failure_metadata(temp_workspace):
        """When a step fails, pipeline should save metadata including errors for the step and pipeline."""
        from analyzer.pipeline.pipeline_commands import PipelineCommand, CommandResult, DataPipeline
        from analyzer.pipeline.metadata import MetadataCollector, MetadataRepository

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir)
            repo = MetadataRepository(storage_path=storage_path)
            collector = MetadataCollector(pipeline_name="failure_pipeline")

            class FailCommand(PipelineCommand):
                def process(self, df: pd.DataFrame | None, context=None) -> CommandResult:
                    return CommandResult(return_code=-1, data=None, error={"message": "simulated failure"})

            pipeline = DataPipeline(commands=[FailCommand()], collector=collector)

            result_df = pipeline.run(repository=repo)

            # run returns empty DataFrame on failure
            assert isinstance(result_df, pd.DataFrame)
            assert result_df.empty

            runs = repo.list_runs()
            assert len(runs) == 1
            loaded = repo.load(runs[0])
            assert loaded is not None
            assert loaded.result_code == -1
            assert loaded.error is not None
            assert loaded.error.get("message") == "simulated failure"
            assert len(loaded.steps) == 1
            assert loaded.steps[0].result_code == -1
            assert loaded.steps[0].error is not None
            assert loaded.steps[0].error.get("message") == "simulated failure"

"""Test - DataPipeline accepts MetadataCollector for metadata tracking."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand
from analyzer.pipeline.metadata import MetadataCollector


class SimpleCommand(PipelineCommand):
    """Simple test command that creates a DataFrame."""
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        return df


def test_data_pipeline_accepts_metadata_collector():
    """Test that DataPipeline can accept a MetadataCollector as optional parameter."""
    commands = [SimpleCommand()]
    collector = MetadataCollector(pipeline_name="test_pipeline")
    
    # DataPipeline should accept collector as optional parameter
    pipeline = DataPipeline(commands, collector=collector)
    
    assert pipeline.collector == collector


def test_data_pipeline_with_no_collector():
    """Test that DataPipeline works without a collector (backward compatible)."""
    commands = [SimpleCommand()]
    
    # DataPipeline should work without collector
    pipeline = DataPipeline(commands)
    
    assert pipeline.collector is None

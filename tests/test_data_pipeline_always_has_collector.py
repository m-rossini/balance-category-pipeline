"""Test DataPipeline always has a collector."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand


class SimpleCommand(PipelineCommand):
    """Simple test command."""
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame({"id": [1, 2, 3]})
        return df


def test_data_pipeline_creates_collector_if_not_provided():
    """Test that DataPipeline creates its own collector if none provided."""
    commands = [SimpleCommand()]
    pipeline = DataPipeline(commands)
    
    # Collector should be created automatically
    assert pipeline.collector is not None
    assert pipeline.collector.pipeline_name is not None


def test_data_pipeline_collector_is_always_present():
    """Test that DataPipeline.run() always uses a collector."""
    commands = [SimpleCommand()]
    pipeline = DataPipeline(commands)
    
    result_df = pipeline.run()
    
    # Metadata should be collected even without explicit collector
    metadata = pipeline.collector.get_pipeline_metadata()
    assert metadata is not None
    assert len(metadata.steps) == 1
    assert metadata.steps[0].name == "SimpleCommand"

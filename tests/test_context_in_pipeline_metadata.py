"""Test that context files are captured in pipeline metadata."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand
from analyzer.pipeline.command_result import CommandResult
from analyzer.pipeline.metadata import MetadataCollector


class ContextAwareCommand(PipelineCommand):
    """Test command that uses context."""
    
    def process(self, df: pd.DataFrame, context=None) -> CommandResult:
        """Return input DataFrame unchanged."""
        return CommandResult(return_code=0, data=df)


def test_pipeline_metadata_includes_context_files():
    """Test that context files are captured in pipeline metadata."""
    context = {
        "categories": "context/candidate_categories.json",
        "typecode": "context/transaction_type_codes.json"
    }
    
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline([ContextAwareCommand()], collector=collector, context=context)
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # Verify context_files is populated
    assert metadata.context_files is not None
    assert metadata.context_files == context


def test_pipeline_metadata_context_files_with_multiple_commands():
    """Test that context is passed through all commands in pipeline."""
    context = {
        "categories": "context/candidate_categories.json",
        "typecode": "context/transaction_type_codes.json"
    }
    
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline(
        [ContextAwareCommand(), ContextAwareCommand(), ContextAwareCommand()],
        collector=collector,
        context=context
    )
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # Verify context_files is populated
    assert metadata.context_files == context


def test_pipeline_without_context():
    """Test that pipeline works without context."""
    collector = MetadataCollector(pipeline_name="test_pipeline")
    pipeline = DataPipeline([ContextAwareCommand()], collector=collector)
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Run pipeline
    pipeline.run(df)
    
    # Get metadata
    metadata = collector.get_pipeline_metadata()
    
    # context_files should be None or empty
    assert metadata.context_files is None or metadata.context_files == {}

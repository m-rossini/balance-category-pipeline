"""Test that SaveFileCommand captures output file path in parameters."""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from analyzer.pipeline.pipeline_commands import DataPipeline, SaveFileCommand
from analyzer.pipeline.metadata import MetadataCollector


def test_save_file_command_captures_file_path_in_parameters():
    """Test that SaveFileCommand saves the full absolute path in step parameters."""
    
    # Create test data
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_output.csv"
        
        collector = MetadataCollector(pipeline_name="test_pipeline")
        pipeline = DataPipeline(
            [SaveFileCommand(output_path=str(output_file))],
            collector=collector
        )
        
        # Run pipeline
        result_df = pipeline.run(df)
        
        # Get metadata
        metadata = collector.get_pipeline_metadata()
        
        # Verify file was saved
        assert output_file.exists()
        
        # Verify parameters contain file path
        assert len(metadata.steps) == 1
        step = metadata.steps[0]
        assert step.parameters is not None
        assert "output_file_path" in step.parameters
        assert step.parameters["output_file_path"] == str(output_file.absolute())


def test_save_file_command_file_path_is_absolute():
    """Test that the saved file path is absolute."""
    
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_output.csv"
        
        collector = MetadataCollector(pipeline_name="test_pipeline")
        pipeline = DataPipeline(
            [SaveFileCommand(output_path=str(output_file))],
            collector=collector
        )
        
        # Run pipeline
        pipeline.run(df)
        
        # Get metadata
        metadata = collector.get_pipeline_metadata()
        
        # Verify file path is absolute
        saved_path = metadata.steps[0].parameters["output_file_path"]
        assert Path(saved_path).is_absolute()

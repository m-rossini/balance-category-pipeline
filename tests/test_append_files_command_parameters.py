"""Test that AppendFilesCommand captures input_dir and file_glob in parameters."""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from analyzer.pipeline.pipeline_commands import DataPipeline, AppendFilesCommand
from analyzer.pipeline.metadata import MetadataCollector


def test_append_files_command_captures_input_dir_and_glob_in_parameters():
    """Test that AppendFilesCommand saves input_dir and file_glob in step parameters."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV files
        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        
        df1 = pd.DataFrame({"col": [1, 2, 3]})
        df1.to_csv(input_dir / "file1.csv", index=False)
        
        df2 = pd.DataFrame({"col": [4, 5, 6]})
        df2.to_csv(input_dir / "file2.csv", index=False)
        
        collector = MetadataCollector(pipeline_name="test_pipeline")
        pipeline = DataPipeline(
            [AppendFilesCommand(input_dir=str(input_dir), file_glob="*.csv")],
            collector=collector
        )
        
        # Run pipeline
        result_df = pipeline.run()
        
        # Get metadata
        metadata = collector.get_pipeline_metadata()
        
        # Verify files were appended
        assert len(result_df) == 6
        
        # Verify parameters contain input_dir and file_glob
        assert len(metadata.steps) == 1
        step = metadata.steps[0]
        assert step.parameters is not None
        assert "input_dir" in step.parameters
        assert "file_glob" in step.parameters
        assert step.parameters["input_dir"] == str(input_dir.absolute())
        assert step.parameters["file_glob"] == "*.csv"


def test_append_files_command_input_dir_is_absolute():
    """Test that the saved input_dir is absolute."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        
        df1 = pd.DataFrame({"col": [1, 2, 3]})
        df1.to_csv(input_dir / "file1.csv", index=False)
        
        collector = MetadataCollector(pipeline_name="test_pipeline")
        pipeline = DataPipeline(
            [AppendFilesCommand(input_dir=str(input_dir), file_glob="*.csv")],
            collector=collector
        )
        
        # Run pipeline
        pipeline.run()
        
        # Get metadata
        metadata = collector.get_pipeline_metadata()
        
        # Verify input_dir is absolute
        saved_dir = metadata.steps[0].parameters["input_dir"]
        assert Path(saved_dir).is_absolute()

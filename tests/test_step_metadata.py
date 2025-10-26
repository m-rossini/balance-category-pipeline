"""Test for StepMetadata - captures metadata of individual pipeline steps."""
import pytest
from datetime import datetime
from analyzer.pipeline.metadata import StepMetadata


def test_step_metadata_creation():
    """Test that StepMetadata can be created with basic information."""
    step_name = "AppendFilesCommand"
    input_rows = 1000
    output_rows = 950
    duration = 1.23
    parameters = {"input_dir": "/data/files", "file_glob": "*.csv"}
    
    metadata = StepMetadata(
        name=step_name,
        input_rows=input_rows,
        output_rows=output_rows,
        duration=duration,
        parameters=parameters
    )
    
    assert metadata.name == step_name
    assert metadata.input_rows == input_rows
    assert metadata.output_rows == output_rows
    assert metadata.duration == duration
    assert metadata.parameters == parameters


def test_step_metadata_with_timestamps():
    """Test that StepMetadata captures start and end times."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 1, 230000)  # 1.23 seconds later
    
    metadata = StepMetadata(
        name="CleanDataCommand",
        input_rows=100,
        output_rows=95,
        start_time=start_time,
        end_time=end_time,
        parameters={}
    )
    
    assert metadata.start_time == start_time
    assert metadata.end_time == end_time
    assert metadata.duration == pytest.approx(1.23, abs=0.01)


def test_step_metadata_without_parameters():
    """Test that StepMetadata can be created without parameters."""
    metadata = StepMetadata(
        name="SaveFileCommand",
        input_rows=100,
        output_rows=100,
        duration=0.5,
        parameters=None
    )
    
    assert metadata.name == "SaveFileCommand"
    assert metadata.parameters == {} or metadata.parameters is None


def test_step_metadata_to_dict():
    """Test that StepMetadata can be serialized to dict."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 1)
    
    metadata = StepMetadata(
        name="MergeFilesCommand",
        input_rows=500,
        output_rows=480,
        start_time=start_time,
        end_time=end_time,
        parameters={"on_columns": ["TransactionNumber"]}
    )
    
    metadata_dict = metadata.to_dict()
    
    assert isinstance(metadata_dict, dict)
    assert metadata_dict["name"] == "MergeFilesCommand"
    assert metadata_dict["input_rows"] == 500
    assert metadata_dict["output_rows"] == 480
    assert metadata_dict["parameters"]["on_columns"] == ["TransactionNumber"]
    assert "start_time" in metadata_dict
    assert "end_time" in metadata_dict

"""Test for StepMetadata - captures metadata of individual pipeline steps."""
import pytest
from datetime import datetime
from analyzer.pipeline.metadata import StepMetadata


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


def test_step_metadata_to_dict():
    """Test that StepMetadata can be serialized to dict."""
    start_time = datetime(2025, 10, 26, 10, 0, 0)
    end_time = datetime(2025, 10, 26, 10, 0, 1)
    
    metadata = StepMetadata(
        name="MergeTrainnedDataCommand",
        input_rows=500,
        output_rows=480,
        start_time=start_time,
        end_time=end_time,
        parameters={"on_columns": ["TransactionNumber"]}
    )
    
    metadata_dict = metadata.to_dict()
    
    assert isinstance(metadata_dict, dict)
    assert metadata_dict["name"] == "MergeTrainnedDataCommand"
    assert metadata_dict["input_rows"] == 500
    assert metadata_dict["output_rows"] == 480
    assert metadata_dict["parameters"]["on_columns"] == ["TransactionNumber"]
    assert "start_time" in metadata_dict
    assert "end_time" in metadata_dict

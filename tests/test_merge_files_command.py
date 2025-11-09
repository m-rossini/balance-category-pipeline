import pytest
import pandas as pd
from tempfile import NamedTemporaryFile
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from analyzer.pipeline.pipeline_commands import MergeTrainnedDataCommand

def test_merge_files_command_updates_categories_from_training_data(test_csv_files):
    """Test that MergeTrainnedDataCommand correctly merges training data into transaction data."""
    # Arrange
    data_df = pd.read_csv(test_csv_files['file1'])
    training_df = pd.read_csv(test_csv_files['training'])
    merge_command = MergeTrainnedDataCommand(input_file=test_csv_files['training'], on_columns=['TransactionNumber'])

    # Act
    result = merge_command.process(data_df)

    # Assert CommandResult contract
    assert result.return_code == 0, f"Expected return_code=0, got {result.return_code}"
    assert result.data is not None, "Expected data to be not None"
    assert result.error is None, f"Expected error=None, got {result.error}"

    result_df = result.data

    # Assert merge behavior: all transaction numbers from original data are present
    assert len(result_df) == len(data_df), "Row count should be preserved after merge"
    assert set(result_df['TransactionNumber']) == set(data_df['TransactionNumber']), \
        "Transaction numbers should match original data"

    # Assert that categories were updated (not None and have meaningful values)
    updated_rows = result_df[result_df['TransactionNumber'].isin(training_df['TransactionNumber'])]
    assert len(updated_rows) > 0, "Some rows should be updated from training data"
    assert updated_rows['CategoryAnnotation'].notna().all(), \
        "Updated rows should have category annotations"
    assert updated_rows['SubCategoryAnnotation'].notna().all(), \
        "Updated rows should have subcategory annotations"
    assert updated_rows['Confidence'].notna().all(), \
        "Updated rows should have confidence values"
    assert (updated_rows['Confidence'] > 0).all() and (updated_rows['Confidence'] <= 1).all(), \
        "Confidence values should be between 0 and 1"

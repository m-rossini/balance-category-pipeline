import pytest
import pandas as pd
from tempfile import NamedTemporaryFile
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from analyzer.pipeline.pipeline_commands import MergeFilesCommand

def test_merge_files_command(test_csv_files):
    # Create temporary data file using fixtures
    data_df = pd.read_csv(test_csv_files['file1'])
    
    # Initialize MergeFilesCommand with fixture training file
    merge_command = MergeFilesCommand(input_file=test_csv_files['training'], on_columns=['TransactionNumber'])

    # Process the merge
    result = merge_command.process(data_df)
    
    # Assert CommandResult structure
    assert result.return_code == 0, f"Expected return_code=0, got {result.return_code}"
    assert result.data is not None, "Expected data to be not None"
    assert result.error is None, f"Expected error=None, got {result.error}"
    # context_updates and metadata_updates are optional
    
    result_df = result.data

    # Debug output on failure: print original, factoids and result
    def debug_print():
        print("--- ORIGINAL DATAFRAME ---")
        print(data_df.to_string(index=False))
        print("--- FACTOIDS DATAFRAME ---")
        print(pd.read_csv(test_csv_files['training']).to_string(index=False))
        print("--- RESULT DATAFRAME ---")
        print(result_df.to_string(index=False))

    # Assertions with debug on failure
    try:
        # Row 0: Should be updated with training data
        assert result_df.loc[0, 'CategoryAnnotation'] == 'Food & Dining'
    except AssertionError:
        debug_print()
        raise
    assert result_df.loc[0, 'SubCategoryAnnotation'] == 'Coffee Shops'
    assert result_df.loc[0, 'Confidence'] == 0.9
    
    # Row 1: Should be updated with training data
    assert result_df.loc[1, 'CategoryAnnotation'] == 'Income'
    assert result_df.loc[1, 'SubCategoryAnnotation'] == 'Salary'
    assert result_df.loc[1, 'Confidence'] == 0.95
    
    # Row 2: Should be updated with training data
    assert result_df.loc[2, 'CategoryAnnotation'] == 'Food & Dining'
    assert result_df.loc[2, 'SubCategoryAnnotation'] == 'Groceries'
    assert result_df.loc[2, 'Confidence'] == 0.88

    print("Test passed: MergeFilesCommand correctly merged the files.")
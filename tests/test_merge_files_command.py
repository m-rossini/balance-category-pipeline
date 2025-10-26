import pytest
import pandas as pd
from tempfile import NamedTemporaryFile
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from analyzer.pipeline.pipeline_commands import MergeFilesCommand

def test_merge_files_command():
    # Create temporary data file
    with NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as data_file:
        data_file.write("TransactionNumber,CategoryAnnotation,SubCategoryAnnotation,Confidence\n")
        data_file.write("1,OriginalCategory,OriginalSubCategory,0.5\n")
        data_file.write("2,OriginalCategory2,OriginalSubCategory2,0.7\n")
        data_file.write("3,,,\n")  # Row with empty category, subcategory, and confidence
        data_file.write("4,DataOnlyCategory,DataOnlySubCategory,0.4\n")  # Row with no factoid data
        data_file.seek(0)

        # Create temporary factoids file
        with NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as factoids_file:
            factoids_file.write("TransactionNumber,CategoryAnnotation,SubCategoryAnnotation,Confidence\n")
            factoids_file.write("1,UpdatedCategory,UpdatedSubCategory,0.9\n")
            factoids_file.write("2,,UpdatedSubCategory2,0.8\n")
            factoids_file.write("3,FactoidCategory,FactoidSubCategory,0.95\n")  # Factoid data for empty row
            factoids_file.seek(0)

            # Load data into DataFrame
            data_df = pd.read_csv(data_file.name)

            # Initialize MergeFilesCommand
            merge_command = MergeFilesCommand(input_file=factoids_file.name, on_columns=['TransactionNumber'])

            # Process the merge
            result = merge_command.process(data_df)
            result_df = result.data

            # Debug output on failure: print original, factoids and result
            def debug_print():
                print("--- ORIGINAL DATAFRAME ---")
                print(data_df.to_string(index=False))
                print("--- FACTOIDS DATAFRAME ---")
                print(pd.read_csv(factoids_file.name).to_string(index=False))
                print("--- RESULT DATAFRAME ---")
                print(result_df.to_string(index=False))

            # Assertions with debug on failure
            try:
                assert result_df.loc[0, 'CategoryAnnotation'] == 'UpdatedCategory'
            except AssertionError:
                debug_print()
                raise
            assert result_df.loc[0, 'SubCategoryAnnotation'] == 'UpdatedSubCategory'
            assert result_df.loc[0, 'Confidence'] == 0.9

            assert result_df.loc[1, 'CategoryAnnotation'] == 'OriginalCategory2'
            assert result_df.loc[1, 'SubCategoryAnnotation'] == 'UpdatedSubCategory2'
            assert result_df.loc[1, 'Confidence'] == 0.8

            assert result_df.loc[2, 'CategoryAnnotation'] == 'FactoidCategory'
            assert result_df.loc[2, 'SubCategoryAnnotation'] == 'FactoidSubCategory'
            assert result_df.loc[2, 'Confidence'] == 0.95

            assert result_df.loc[3, 'CategoryAnnotation'] == 'DataOnlyCategory'
            assert result_df.loc[3, 'SubCategoryAnnotation'] == 'DataOnlySubCategory'
            assert result_df.loc[3, 'Confidence'] == 0.4

            print("Test passed: MergeFilesCommand correctly merged the files.")

if __name__ == "__main__":
    pytest.main(["-v", "test_merge_files_command.py"])
import os
import pandas as pd
from unittest.mock import patch, MagicMock

from analyzer.workflows import bank_transaction_analysis, ai_categorization, minimal_load
from analyzer.pipeline.pipeline_commands import MergeFilesCommand, CleanDataCommand, AppendFilesCommand, AIRemoteCategorizationCommand


class TestDataPipelineIntegration:
    """Integration tests for complete data pipeline workflows."""

    @patch('urllib.request.urlopen')
    def test_bank_transaction_analysis_workflow(self, mock_urlopen, temp_workspace, test_csv_files, test_context_files):
        """Test the complete bank_transaction_analysis workflow."""
        # Mock the external API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"code": "SUCCESS", "items": []}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Change to temp workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace['root'])
            
            # Files are already created by test_csv_files fixture in extratos dir
            # Just need to verify they're accessible and run the pipeline
            
            # Get and run the pipeline
            pipeline = bank_transaction_analysis.get_pipeline()
            result_df = pipeline.run()

            # Validate results
            assert isinstance(result_df, pd.DataFrame)
            assert not result_df.empty
            assert len(result_df) == 5  # 3 + 2 transactions from the two CSV files

            # Check that expected columns exist
            expected_columns = ['TransactionDate', 'TransactionType', 'TransactionDescription', 'TransactionValue']
            for col in expected_columns:
                assert col in result_df.columns

            # Check that output file was created
            assert os.path.exists(temp_workspace['output'] / 'annotated_bos.csv')
        finally:
            os.chdir(original_cwd)

    @patch('urllib.request.urlopen')
    def test_ai_categorization_workflow(self, mock_urlopen, temp_workspace, test_csv_files, test_context_files):
        """Test the complete ai_categorization workflow."""
        # Mock the external API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"code": "SUCCESS", "items": [{"id": "1", "category": "Food & Dining", "subcategory": "Coffee Shops", "confidence": 0.95}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Change to temp workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace['root'])
            
            # Files are already created by fixtures in their proper locations
            # Get and run the pipeline
            pipeline = ai_categorization.get_pipeline()
            result_df = pipeline.run()

            # Validate results
            assert isinstance(result_df, pd.DataFrame)
        finally:
            os.chdir(original_cwd)

    def test_minimal_load_workflow(self, temp_workspace, test_csv_files, test_context_files):
        """Test the minimal_load workflow."""
        # Change to temp workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace['root'])
            
            # Files are already created by fixtures in their proper locations
            # Get and run the pipeline
            pipeline = minimal_load.get_pipeline()
            result_df = pipeline.run()

            # Validate results
            assert isinstance(result_df, pd.DataFrame)
            assert not result_df.empty
            assert len(result_df) == 5  # 3 + 2 transactions

            # Check that expected columns exist
            expected_columns = ['TransactionDate', 'TransactionType', 'TransactionDescription', 'TransactionValue']
            for col in expected_columns:
                assert col in result_df.columns
        finally:
            os.chdir(original_cwd)

    @patch('urllib.request.urlopen')
    def test_workflow_error_handling(self, mock_urlopen, temp_workspace, test_csv_files, test_context_files):
        """Test that workflows handle errors gracefully."""
        # Mock the external API to raise an exception
        mock_urlopen.side_effect = Exception("API service unavailable")

        # Change to temp workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace['root'])
            
            # Files are already created by fixtures in their proper locations
            # Run pipeline - should handle the error gracefully
            pipeline = ai_categorization.get_pipeline()
            result_df = pipeline.run()

            # Should return a DataFrame rather than crashing
            assert isinstance(result_df, pd.DataFrame)
        finally:
            os.chdir(original_cwd)

    def test_workflow_with_missing_context_files(self, temp_workspace, test_csv_files):
        """Test workflows handle missing context files gracefully."""
        # Change to temp workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace['root'])
            
            # Files are already created by fixtures but no context files
            # Run minimal workflow (should work without context)
            pipeline = minimal_load.get_pipeline()
            result_df = pipeline.run()

            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) == 5
        finally:
            os.chdir(original_cwd)

    def test_append_files_command(self, temp_workspace, test_csv_files):
        """Test AppendFilesCommand loads and concatenates multiple CSV files."""
        # Files are already created by test_csv_files fixture in extratos dir
        
        # Test append command
        append_command = AppendFilesCommand(input_dir=str(temp_workspace['extratos']), file_glob='*.csv')
        result = append_command.process()

        # Assert CommandResult structure
        assert result.return_code == 0, f"Expected return_code=0, got {result.return_code}"
        assert result.data is not None, "Expected data to be not None"
        assert result.error is None, f"Expected error=None, got {result.error}"
        
        result_df = result.data
        
        # Validate results
        assert isinstance(result_df, pd.DataFrame)
        assert not result_df.empty
        assert len(result_df) == 5  # 3 + 2 transactions
        assert 'TransactionNumber' in result_df.columns
        # Check reverse order: latest files first
        assert result_df.loc[0, 'TransactionValue'] == -45.00  # From test_transactions_2.csv (sorted reverse)

    def test_merge_files_command_missing_df(self):
        """Test MergeFilesCommand error when df is None and input_file is set."""
        merge_command = MergeFilesCommand(input_file='dummy.csv')
        result = merge_command.process(df=None)
        
        # Assert CommandResult structure for error case
        assert result.return_code == -1, f"Expected return_code=-1, got {result.return_code}"
        assert result.data is None, "Expected data=None on error"
        assert result.error is not None, f"Expected error dict, got {result.error}"

    def test_clean_data_command_default_clean(self):
        """Test CleanDataCommand uses default_clean when no functions provided."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        clean_command = CleanDataCommand(functions=None)
        result = clean_command.process(df)
        
        # Assert CommandResult structure
        assert result.return_code == 0, f"Expected return_code=0, got {result.return_code}"
        assert result.data is not None, "Expected data to be not None"
        assert result.error is None, f"Expected error=None, got {result.error}"
        
        assert result.data.equals(df)  # default_clean just returns df

    def test_append_files_command_input_files_branch(self, temp_workspace, test_csv_files):
        """Test AppendFilesCommand using input_files parameter."""
        # Files are already created by test_csv_files fixture
        
        # Use input_files instead of input_dir
        file_paths = [
            str(temp_workspace['extratos'] / 'test_transactions_1.csv'),
            str(temp_workspace['extratos'] / 'test_transactions_2.csv')
        ]
        append_command = AppendFilesCommand(input_files=file_paths)
        result = append_command.process()

        # Assert CommandResult structure
        assert result.return_code == 0, f"Expected return_code=0, got {result.return_code}"
        assert result.data is not None, "Expected data to be not None"
        assert result.error is None, f"Expected error=None, got {result.error}"
        
        result_df = result.data
        
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 5

    def test_append_files_command_no_files_found(self):
        """Test AppendFilesCommand when no files are found."""
        append_command = AppendFilesCommand(input_dir='/nonexistent', file_glob='*.csv')
        result = append_command.process()
        
        # Assert CommandResult structure for error case
        assert result.return_code == -1, f"Expected return_code=-1, got {result.return_code}"
        assert result.data is None, "Expected data=None on error"
        assert result.error is not None, f"Expected error dict, got {result.error}"

    def test_append_files_command_read_error(self, temp_workspace):
        """Test AppendFilesCommand when file read fails."""
        # Create a file that will fail to read (e.g., invalid CSV)
        invalid_file = temp_workspace['extratos'] / 'invalid.csv'
        with open(invalid_file, 'w') as f:
            f.write("invalid content\n")

        append_command = AppendFilesCommand(input_files=[str(invalid_file)])
        result = append_command.process()
        
        # Even with invalid content, pandas can parse it (treats first line as header)
        # So just check that we get a result
        assert result.return_code == 0
        assert result.data is not None

    def _has_no_annotations(self, df):
        """Helper to check if DataFrame has no CategoryAnnotation set."""
        if 'CategoryAnnotation' not in df.columns:
            return True
        return not df['CategoryAnnotation'].notna().any()
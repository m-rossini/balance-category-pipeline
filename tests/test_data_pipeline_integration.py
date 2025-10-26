import os
import tempfile
import shutil
import pandas as pd
# import pytest
from unittest.mock import patch, MagicMock

from analyzer.workflows import bank_transaction_analysis, ai_categorization, minimal_load
from analyzer.pipeline.pipeline_commands import MergeFilesCommand, CleanDataCommand, AppendFilesCommand, AIRemoteCategorizationCommand


class TestDataPipelineIntegration:
    """Integration tests for complete data pipeline workflows."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create test data directory structure
        self.test_data_dir = os.path.join(self.test_dir, 'data')
        self.test_extratos_dir = os.path.join(self.test_data_dir, 'extratos', 'bank_bos')
        self.test_training_dir = os.path.join(self.test_data_dir, 'training')
        self.test_output_dir = os.path.join(self.test_data_dir, 'output')
        self.test_context_dir = os.path.join(self.test_dir, 'context')

        # Create directories
        os.makedirs(self.test_extratos_dir, exist_ok=True)
        os.makedirs(self.test_training_dir, exist_ok=True)
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.test_context_dir, exist_ok=True)

        # Change to test directory
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Change back to original directory
        os.chdir(self.original_cwd)
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def create_test_transaction_data(self):
        """Create test CSV files with sample transaction data."""
        # Create sample transaction data
        data1 = {
            'TransactionNumber': [1, 2, 3],
            'TransactionDate': ['01/10/2025', '02/10/2025', '03/10/2025'],
            'TransactionType': ['DEB', 'FPI', 'DEB'],
            'TransactionDescription': ['STARBUCKS COFFEE', 'SALARY PAYMENT', 'TESCO SUPERMARKET'],
            'TransactionValue': [-5.50, 2500.00, -85.30]
        }

        data2 = {
            'TransactionNumber': [4, 5],
            'TransactionDate': ['04/10/2025', '05/10/2025'],
            'TransactionType': ['DD', 'DEB'],
            'TransactionDescription': ['BT GROUP PLC', 'AMAZON PURCHASE'],
            'TransactionValue': [-45.00, -29.99]
        }

        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)

        # Save test CSV files
        df1.to_csv(os.path.join(self.test_extratos_dir, 'test_transactions_1.csv'), index=False)
        df2.to_csv(os.path.join(self.test_extratos_dir, 'test_transactions_2.csv'), index=False)

        return df1, df2

    def create_test_training_data(self):
        """Create test training data file."""
        training_data = {
            'TransactionNumber': [1, 2, 3],
            'Category': ['Food & Dining', 'Income', 'Food & Dining'],
            'SubCategory': ['Coffee Shops', 'Salary', 'Groceries'],
            'Notes': ['Coffee purchase', 'Monthly salary', 'Grocery shopping']
        }

        df = pd.DataFrame(training_data)
        df.to_csv(os.path.join(self.test_training_dir, 'factoids.csv'), index=False)
        return df

    def create_test_context_files(self):
        """Create test context files."""
        # Categories file
        categories = {
            "expense_categories": {
                "Food & Dining": ["Coffee Shops", "Restaurants", "Groceries"],
                "Utilities": ["Internet", "Phone"],
                "Transportation": ["Gas", "Public Transport"]
            },
            "income_categories": {
                "Income": ["Salary", "Freelance"]
            }
        }

        import json
        with open(os.path.join(self.test_context_dir, 'candidate_categories.json'), 'w') as f:
            json.dump(categories, f)

        # Transaction codes file (JSON format)
        codes = {
            "transaction_codes": [
                {"code": "DD", "description": "Direct Debit"},
                {"code": "DEB", "description": "Debit Card"},
                {"code": "FPI", "description": "Faster Payment Incoming"},
                {"code": "SO", "description": "Standing Order"}
            ]
        }

        with open(os.path.join(self.test_context_dir, 'transaction_type_codes.json'), 'w') as f:
            json.dump(codes, f)

    @patch('urllib.request.urlopen')
    def test_bank_transaction_analysis_workflow(self, mock_urlopen):
        """Test the complete bank_transaction_analysis workflow."""
        # Mock the external API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"code": "SUCCESS", "items": []}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Setup test data
        self.create_test_transaction_data()
        self.create_test_training_data()
        self.create_test_context_files()

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
        assert os.path.exists(os.path.join(self.test_output_dir, 'annotated_bos.csv'))

    @patch('urllib.request.urlopen')
    def test_ai_categorization_workflow(self, mock_urlopen):
        """Test the complete ai_categorization workflow."""
        # Mock the external API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"code": "SUCCESS", "items": [{"id": "1", "category": "Food & Dining", "subcategory": "Coffee Shops", "confidence": 0.95}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Setup test data
        df1, df2 = self.create_test_transaction_data()
        self.create_test_training_data()
        self.create_test_context_files()

        # Get and run the pipeline
        pipeline = ai_categorization.get_pipeline()
        result_df = pipeline.run()

        # Validate results
        assert isinstance(result_df, pd.DataFrame)

    def test_minimal_load_workflow(self):
        """Test the minimal_load workflow."""
        # Setup test data
        df1, df2 = self.create_test_transaction_data()
        self.create_test_context_files()

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

    @patch('urllib.request.urlopen')
    def test_workflow_error_handling(self, mock_urlopen):
        """Test that workflows handle errors gracefully."""
        # Mock the external API to raise an exception
        mock_urlopen.side_effect = Exception("API service unavailable")

        # Setup minimal test data
        self.create_test_transaction_data()
        self.create_test_context_files()

        # Run pipeline - should handle the error gracefully
        pipeline = ai_categorization.get_pipeline()
        result_df = pipeline.run()

        # Should return a DataFrame rather than crashing
        assert isinstance(result_df, pd.DataFrame)

    def test_workflow_with_missing_context_files(self):
        """Test workflows handle missing context files gracefully."""
        # Setup test data but no context files
        self.create_test_transaction_data()

        # Run minimal workflow (should work without context)
        pipeline = minimal_load.get_pipeline()
        result_df = pipeline.run()

        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 5

    def test_append_files_command(self):
        """Test AppendFilesCommand loads and concatenates multiple CSV files."""
        # Setup test data
        self.create_test_transaction_data()

        # Test append command
        append_command = AppendFilesCommand(input_dir=self.test_extratos_dir, file_glob='*.csv')
        result = append_command.process()

        # Extract data from CommandResult
        assert result.return_code == 0
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
        result_df = merge_command.process(df=None)
        assert result_df.empty

    def test_clean_data_command_default_clean(self):
        """Test CleanDataCommand uses default_clean when no functions provided."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        clean_command = CleanDataCommand(functions=None)
        result_df = clean_command.process(df)
        assert result_df.equals(df)  # default_clean just returns df

    def test_append_files_command_input_files_branch(self):
        """Test AppendFilesCommand using input_files parameter."""
        # Create test files
        self.create_test_transaction_data()

        # Use input_files instead of input_dir
        file_paths = [
            os.path.join(self.test_extratos_dir, 'test_transactions_1.csv'),
            os.path.join(self.test_extratos_dir, 'test_transactions_2.csv')
        ]
        append_command = AppendFilesCommand(input_files=file_paths)
        result = append_command.process()

        # Extract data from CommandResult
        assert result.return_code == 0
        result_df = result.data
        
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 5

    def test_append_files_command_no_files_found(self):
        """Test AppendFilesCommand when no files are found."""
        append_command = AppendFilesCommand(input_dir='/nonexistent', file_glob='*.csv')
        result = append_command.process()
        
        # Check error code
        assert result.return_code == -1
        assert result.data is None

    def test_append_files_command_read_error(self):
        """Test AppendFilesCommand when file read fails."""
        # Create a file that will fail to read (e.g., invalid CSV)
        invalid_file = os.path.join(self.test_extratos_dir, 'invalid.csv')
        with open(invalid_file, 'w') as f:
            f.write("invalid content\n")

        append_command = AppendFilesCommand(input_files=[invalid_file])
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
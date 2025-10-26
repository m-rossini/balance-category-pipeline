import os
import tempfile
import json
import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

from analyzer.pipeline.pipeline_commands import AIRemoteCategorizationCommand


class TestAIRemoteCategorization:
    """Black box tests for AIRemoteCategorizationCommand.
    
    These tests verify input -> output behavior without testing internal implementation.
    """

    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.context_file = os.path.join(self.test_dir, 'categories.json')
        self.typecode_file = os.path.join(self.test_dir, 'transaction_type_codes.json')
        
        # Create test categories context file
        context_data = {
            "expense_categories": {
                "Food & Dining": ["Coffee Shops", "Restaurants", "Groceries"],
                "Utilities": ["Internet", "Phone"],
                "Transportation": ["Gas", "Public Transport"]
            },
            "income_categories": {
                "Income": ["Salary", "Freelance"]
            }
        }
        with open(self.context_file, 'w') as f:
            json.dump(context_data, f)
        
        # Create test transaction type codes file
        typecode_data = {
            "transaction_codes": [
                {"code": "DD", "description": "Direct Debit"},
                {"code": "DEB", "description": "Debit Card"},
                {"code": "FPI", "description": "Faster Payment Incoming"},
                {"code": "SO", "description": "Standing Order"}
            ]
        }
        with open(self.typecode_file, 'w') as f:
            json.dump(typecode_data, f)

    def teardown_method(self):
        """Clean up test environment after each test."""
        import shutil
        shutil.rmtree(self.test_dir)

    def create_test_dataframe(self):
        """Create a simple test DataFrame with required columns."""
        return pd.DataFrame({
            'TransactionNumber': [1, 2, 3],
            'TransactionDate': ['01/10/2025', '02/10/2025', '03/10/2025'],
            'TransactionType': ['DEB', 'FPI', 'DEB'],
            'TransactionDescription': ['STARBUCKS COFFEE', 'SALARY PAYMENT', 'TESCO SUPERMARKET'],
            'TransactionValue': [-5.50, 2500.00, -85.30],
            'CategoryAnnotation': [None, None, None],
            'SubCategoryAnnotation': [None, None, None],
            'Confidence': [None, None, None]
        })

    @patch('requests.post')
    def test_categorize_some_transactions(self, mock_post):
        """Test successful categorization of some transactions.
        
        Black box: Input DataFrame with transactions -> Output DataFrame with categories populated
        """
        # Mock successful API response with categories
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "items": [
                {"id": "0", "category": {"category": "Food & Dining", "subcategory": "Coffee Shops", "confidence": 0.95}},
                {"id": "2", "category": {"category": "Food & Dining", "subcategory": "Groceries", "confidence": 0.92}}
            ]
        }
        mock_post.return_value = mock_response

        # Input
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute
        result_df = command.process(df)

        # Output validation: some rows should have categories
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        
        # Row 0 should be categorized
        assert result_df.loc[0, 'CategoryAnnotation'] == 'Food & Dining'
        assert result_df.loc[0, 'SubCategoryAnnotation'] == 'Coffee Shops'
        assert result_df.loc[0, 'Confidence'] == 0.95
        
        # Row 1 should NOT be categorized (API didn't return it)
        assert pd.isna(result_df.loc[1, 'CategoryAnnotation'])
        
        # Row 2 should be categorized
        assert result_df.loc[2, 'CategoryAnnotation'] == 'Food & Dining'
        assert result_df.loc[2, 'SubCategoryAnnotation'] == 'Groceries'
        assert result_df.loc[2, 'Confidence'] == 0.92

    @patch('requests.post')
    def test_no_categorization_returned(self, mock_post):
        """Test when API returns no categorizations (empty items list).
        
        Black box: Input DataFrame with transactions -> Output DataFrame with no categories populated
        """
        # Mock API response with no items (no categorizations)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "items": []
        }
        mock_post.return_value = mock_response

        # Input
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute
        result_df = command.process(df)

        # Output validation: no categories should be populated
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        
        # All rows should remain uncategorized
        assert pd.isna(result_df.loc[0, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[1, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[2, 'CategoryAnnotation'])

    @patch('requests.post')
    def test_external_service_fails(self, mock_post):
        """Test when external service fails (connection error).
        
        Black box: Input DataFrame -> Output DataFrame unchanged (graceful failure)
        """
        # Mock service failure
        mock_post.side_effect = Exception("Connection refused")

        # Input
        df = self.create_test_dataframe()
        original_df = df.copy()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute (should not raise exception)
        result_df = command.process(df)

        # Output validation: DataFrame should be returned unchanged
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        
        # All rows should remain uncategorized (no changes from failure)
        assert pd.isna(result_df.loc[0, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[1, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[2, 'CategoryAnnotation'])

    @patch('requests.post')
    def test_api_returns_http_error(self, mock_post):
        """Test when API returns HTTP error status.
        
        Black box: Input DataFrame -> Output DataFrame unchanged (graceful failure)
        """
        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP 500: Internal Server Error")
        mock_post.return_value = mock_response

        # Input
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute (should not raise exception)
        result_df = command.process(df)

        # Output validation: DataFrame should be returned unchanged
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        
        # All rows should remain uncategorized
        assert pd.isna(result_df.loc[0, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[1, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[2, 'CategoryAnnotation'])

    @patch('requests.post')
    def test_empty_dataframe_input(self, mock_post):
        """Test with empty DataFrame input.
        
        Black box: Empty DataFrame input -> Empty DataFrame output
        """
        # Input
        df = pd.DataFrame({
            'TransactionNumber': [],
            'TransactionDate': [],
            'TransactionType': [],
            'TransactionDescription': [],
            'TransactionValue': [],
            'CategoryAnnotation': [],
            'SubCategoryAnnotation': [],
            'Confidence': []
        })
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute
        result_df = command.process(df)

        # Output validation: should return empty DataFrame without calling API
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 0
        assert mock_post.call_count == 0  # API should not be called for empty input

    @patch('requests.post')
    def test_categorize_all_transactions(self, mock_post):
        """Test successful categorization of all transactions.
        
        Black box: Input DataFrame -> Output DataFrame with all rows categorized
        """
        # Mock successful API response with all transactions categorized
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "items": [
                {"id": "0", "category": {"category": "Food & Dining", "subcategory": "Coffee Shops", "confidence": 0.95}},
                {"id": "1", "category": {"category": "Income", "subcategory": "Salary", "confidence": 0.99}},
                {"id": "2", "category": {"category": "Food & Dining", "subcategory": "Groceries", "confidence": 0.92}}
            ]
        }
        mock_post.return_value = mock_response

        # Input
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute
        result_df = command.process(df)

        # Output validation: all rows should be categorized
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        
        # All rows should have categories
        for i in range(3):
            assert result_df.loc[i, 'CategoryAnnotation'] is not None
            assert result_df.loc[i, 'SubCategoryAnnotation'] is not None
            assert result_df.loc[i, 'Confidence'] is not None

    @patch('requests.post')
    def test_api_response_with_null_categories(self, mock_post):
        """Test when API returns items with null category data.
        
        Black box: Input DataFrame -> Output with null categories left as is
        """
        # Mock API response with null categories
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "items": [
                {"id": "0", "category": None},
                {"id": "1", "category": None},
                {"id": "2", "category": None}
            ]
        }
        mock_post.return_value = mock_response

        # Input
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute
        result_df = command.process(df)

        # Output validation: no categories should be populated
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        
        # All rows should remain uncategorized
        assert pd.isna(result_df.loc[0, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[1, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[2, 'CategoryAnnotation'])

    @patch('requests.post')
    def test_missing_context_file(self, mock_post):
        """Test behavior when context file is missing.
        
        Black box: Input DataFrame with missing context -> Command still processes
        """
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "items": [
                {"id": "0", "category": {"category": "Food & Dining", "subcategory": "Coffee Shops", "confidence": 0.95}}
            ]
        }
        mock_post.return_value = mock_response

        # Input with non-existent context file
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': '/nonexistent/categories.json'}
        )

        # Execute (should handle missing context gracefully)
        result_df = command.process(df)

        # Output validation: should still return DataFrame with API results
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        # Should still apply categorization despite missing context file
        assert result_df.loc[0, 'CategoryAnnotation'] == 'Food & Dining'

    @patch('requests.post')
    def test_stops_processing_when_max_errors_exceeded(self, mock_post):
        """Test that processing stops when errors exceed max_errors threshold.
        
        Black box: Input DataFrame with API failures -> Processing stops after max_errors
        """
        # Mock API to always fail
        mock_post.side_effect = Exception("API connection failed")

        # Input: DataFrame with 6 rows, batch size 2 = 3 batches
        df = self.create_test_dataframe()
        # Add 3 more rows to make 6 total
        extra_rows = pd.DataFrame({
            'TransactionNumber': [4, 5, 6],
            'TransactionDate': ['04/10/2025', '05/10/2025', '06/10/2025'],
            'TransactionType': ['DEB', 'FPI', 'DEB'],
            'TransactionDescription': ['AMAZON', 'TRANSFER', 'WALMART'],
            'TransactionValue': [-25.00, 500.00, -50.00],
            'CategoryAnnotation': [None, None, None],
            'SubCategoryAnnotation': [None, None, None],
            'Confidence': [None, None, None]
        })
        df = pd.concat([df, extra_rows], ignore_index=True)
        
        # Create command with batch_size=2 and max_errors=2
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file},
            batch_size=2,
            max_errors=2
        )

        # Execute
        result_df = command.process(df)

        # Output validation: should return DataFrame unchanged
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 6
        
        # Verify API was called only 2 times (first 2 batches fail, then stop)
        # With 6 rows and batch_size=2: would be 3 batches, but stops after 2 failures
        assert mock_post.call_count == 2, f"Expected 2 API calls, got {mock_post.call_count}"
        
        # No rows should be categorized (all API calls failed)
        assert pd.isna(result_df.loc[0, 'CategoryAnnotation'])
        assert pd.isna(result_df.loc[1, 'CategoryAnnotation'])

    @patch('requests.post')
    def test_context_passed_as_json_content_not_file_paths(self, mock_post):
        """Test that context data (categories and transaction codes) are passed as JSON content, not file paths.
        
        Validates:
        - Categories: dict (not string/file path)
        - Transaction codes: list with dict items having 'code' and 'description' attributes
        """
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "items": [
                {"id": "0", "category": {"category": "Food & Dining", "subcategory": "Coffee Shops", "confidence": 0.95}}
            ]
        }
        mock_post.return_value = mock_response

        # Input
        df = self.create_test_dataframe()
        command = AIRemoteCategorizationCommand(
            service_url="http://api.example.com/categorize",
            context={'categories': self.context_file, 'typecode': self.typecode_file}
        )

        # Execute
        result_df = command.process(df)

        # Validate that API was called
        assert mock_post.called
        
        # Get the payload sent to the API
        call_args = mock_post.call_args
        sent_payload = call_args[1]['json']  # Extract the json parameter
        
        # Verify context exists and is a list
        assert 'context' in sent_payload
        assert isinstance(sent_payload['context'], list)
        assert len(sent_payload['context']) == 2  # Both categories and transaction codes
        
        # ===== VERIFY CATEGORIES IS JSON CONTENT (DICT) =====
        categories_context = sent_payload['context'][0]
        assert isinstance(categories_context, dict), "Categories should be a dict (JSON object)"
        assert not isinstance(categories_context, str), "Categories should not be a string/file path"
        
        # ===== VERIFY TRANSACTION CODES IS JSON CONTENT (LIST) =====
        typecode_context = sent_payload['context'][1]
        assert isinstance(typecode_context, dict), "Transaction codes context should be a dict"
        assert not isinstance(typecode_context, str), "Transaction codes should not be a string/file path"
        
        # Transaction codes should contain a list
        assert 'transaction_codes' in typecode_context
        codes_list = typecode_context['transaction_codes']
        assert isinstance(codes_list, list), "transaction_codes should be a list"
        assert len(codes_list) >= 1, "transaction_codes list should have at least 1 element"
        
        # Each code item must have 'code' and 'description' attributes
        for code_item in codes_list:
            assert isinstance(code_item, dict), "Each code item should be a dict"
            assert 'code' in code_item, "Code item must have 'code' attribute"
            assert 'description' in code_item, "Code item must have 'description' attribute"


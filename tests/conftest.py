"""Shared test fixtures and utilities for all tests.

This module provides reusable fixtures and helper classes to reduce test code repetition
and improve maintainability. All fixtures follow pytest conventions and can be used
across the entire test suite.
"""
import pytest
import pandas as pd
import tempfile
import os
import json
import sys
from pathlib import Path

# Add src directory to Python path so we can import analyzer modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from analyzer.pipeline.pipeline_commands import PipelineCommand, CommandResult
from analyzer.pipeline.metadata import MetadataCollector


# ============================================================================
# Test Command Classes (reusable across all tests)
# ============================================================================

class SimpleCommand(PipelineCommand):
    """Minimal command for testing - returns DataFrame unchanged."""
    def process(self, df: pd.DataFrame, context=None) -> CommandResult:
        if df is None or df.empty:
            df = pd.DataFrame({"id": [1, 2, 3]})
        return CommandResult(return_code=0, data=df)


class MockLoadCommand(PipelineCommand):
    """Mock command that loads categorized data with good confidence."""
    def process(self, df: pd.DataFrame, context=None) -> CommandResult:
        data = pd.DataFrame({
            'CategoryAnnotation': ['Food', 'Transport', 'Utilities', 'Entertainment'],
            'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric', 'Movie'],
            'Confidence': [0.95, 0.92, 0.88, 0.75],
            'Amount': [5.50, 25.00, 120.00, 15.00]
        })
        return CommandResult(return_code=0, data=data)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def simple_transaction_dataframe():
    """DataFrame with basic transaction data (3 transactions)."""
    return pd.DataFrame({
        'TransactionNumber': [1, 2, 3],
        'TransactionDate': ['01/10/2025', '02/10/2025', '03/10/2025'],
        'TransactionType': ['DEB', 'FPI', 'DEB'],
        'TransactionDescription': ['STARBUCKS COFFEE', 'SALARY PAYMENT', 'TESCO SUPERMARKET'],
        'TransactionValue': [-5.50, 2500.00, -85.30]
    })


@pytest.fixture
def extended_transaction_dataframe():
    """DataFrame with extended transaction data (5 transactions total)."""
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
    return pd.concat([pd.DataFrame(data1), pd.DataFrame(data2)], ignore_index=True)


@pytest.fixture
def categorized_dataframe_good_confidence():
    """DataFrame with high confidence categorization."""
    return pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric'],
        'Confidence': [0.95, 0.92, 0.88]
    })


@pytest.fixture
def categorized_dataframe_mixed_confidence():
    """DataFrame with mixed confidence levels including some missing data."""
    return pd.DataFrame({
        'CategoryAnnotation': ['Food', None, 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', None],
        'Confidence': [0.95, 0.92, 0.88]
    })


@pytest.fixture
def categorized_dataframe_low_confidence():
    """DataFrame with consistently low confidence scores."""
    return pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', 'Gas'],
        'Confidence': [0.45, 0.52, 0.48]
    })


@pytest.fixture
def empty_categorized_dataframe():
    """Empty DataFrame with categorization columns."""
    return pd.DataFrame({
        'CategoryAnnotation': [],
        'SubCategoryAnnotation': [],
        'Confidence': []
    })


# ============================================================================
# Temporary Directory and File Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace():
    """Temporary workspace with standard data directory structure.
    
    Creates:
        - data/extratos/bank_bos/
        - data/training/
        - data/output/
        - context/
    
    Yields:
        dict with paths to each directory
    
    Cleanup: Automatic via pytest
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        paths = {
            'root': tmpdir,
            'data': tmpdir_path / 'data',
            'extratos': tmpdir_path / 'data' / 'extratos' / 'bank_bos',
            'training': tmpdir_path / 'data' / 'training',
            'output': tmpdir_path / 'data' / 'output',
            'context': tmpdir_path / 'context',
        }
        
        # Create all directories
        for path in paths.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        yield paths


@pytest.fixture
def test_csv_files(temp_workspace):
    """Create test CSV files in temp workspace.
    
    Creates:
        - 2 transaction files with sample data
        - 1 training file with factoids
    
    Yields:
        dict with file paths
    """
    paths = {
        'file1': temp_workspace['extratos'] / 'test_transactions_1.csv',
        'file2': temp_workspace['extratos'] / 'test_transactions_2.csv',
        'training': temp_workspace['training'] / 'factoids.csv',
    }
    
    # Write file 1
    df1 = pd.DataFrame({
        'TransactionNumber': [1, 2, 3],
        'TransactionDate': ['01/10/2025', '02/10/2025', '03/10/2025'],
        'TransactionType': ['DEB', 'FPI', 'DEB'],
        'TransactionDescription': ['STARBUCKS COFFEE', 'SALARY PAYMENT', 'TESCO SUPERMARKET'],
        'TransactionValue': [-5.50, 2500.00, -85.30]
    })
    df1.to_csv(paths['file1'], index=False)
    
    # Write file 2
    df2 = pd.DataFrame({
        'TransactionNumber': [4, 5],
        'TransactionDate': ['04/10/2025', '05/10/2025'],
        'TransactionType': ['DD', 'DEB'],
        'TransactionDescription': ['BT GROUP PLC', 'AMAZON PURCHASE'],
        'TransactionValue': [-45.00, -29.99]
    })
    df2.to_csv(paths['file2'], index=False)
    
    # Write training file
    df_training = pd.DataFrame({
        'TransactionNumber': [1, 2, 3],
        'CategoryAnnotation': ['Food & Dining', 'Income', 'Food & Dining'],
        'SubCategoryAnnotation': ['Coffee Shops', 'Salary', 'Groceries'],
        'Confidence': [0.9, 0.95, 0.88]
    })
    df_training.to_csv(paths['training'], index=False)
    
    yield paths


@pytest.fixture
def test_context_files(temp_workspace):
    """Create test context JSON files.
    
    Creates:
        - candidate_categories.json
        - transaction_type_codes.json
    
    Yields:
        dict with file paths
    """
    paths = {
        'categories': temp_workspace['context'] / 'candidate_categories.json',
        'typecodes': temp_workspace['context'] / 'transaction_type_codes.json',
    }
    
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
    
    typecodes = {
        "transaction_codes": [
            {"code": "DD", "description": "Direct Debit"},
            {"code": "DEB", "description": "Debit Card"},
            {"code": "FPI", "description": "Faster Payment Incoming"},
            {"code": "SO", "description": "Standing Order"}
        ]
    }
    
    with open(paths['categories'], 'w') as f:
        json.dump(categories, f)
    
    with open(paths['typecodes'], 'w') as f:
        json.dump(typecodes, f)
    
    yield paths


# ============================================================================
# Metadata and Collector Fixtures
# ============================================================================

@pytest.fixture
def metadata_collector():
    """Create a MetadataCollector instance."""
    return MetadataCollector(pipeline_name="test_pipeline")


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_command_result_success(result):
    """Assert that a CommandResult indicates success.
    
    Checks:
        - return_code == 0
        - data is not None
        - error is None
    """
    assert result.return_code == 0, f"Expected return_code=0, got {result.return_code}"
    assert result.data is not None, "Expected data to be not None"
    assert result.error is None, f"Expected error=None, got {result.error}"


def assert_command_result_failure(result, expected_return_code=-1):
    """Assert that a CommandResult indicates failure.
    
    Args:
        result: CommandResult to check
        expected_return_code: Expected negative return code (default: -1)
    """
    assert result.return_code == expected_return_code, \
        f"Expected return_code={expected_return_code}, got {result.return_code}"
    assert result.error is not None, "Expected error to be not None"


def assert_dataframe_structure(df, expected_columns, min_rows=1):
    """Assert that a DataFrame has expected structure.
    
    Args:
        df: DataFrame to check
        expected_columns: List of column names that should exist
        min_rows: Minimum number of rows (default: 1)
    """
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= min_rows, f"Expected at least {min_rows} rows, got {len(df)}"
    for col in expected_columns:
        assert col in df.columns, f"Expected column '{col}' not found"

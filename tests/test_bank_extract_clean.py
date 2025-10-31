import pandas as pd
from analyzer.workflows.bank_extract_clean import bank_extract_clean


def test_bank_extract_clean_removes_intermediate_columns():
    """Test that bank_extract_clean removes Debit/Credit columns."""
    data = [
        {
            'Transaction Date': '01/01/2020',
            'Transaction Type': 'DEB',
            "Sort Code": "'80-49-57",
            'Account Number': 123,
            'Transaction Description': 'Test Debit',
            'Debit Amount': '10.50',
            'Credit Amount': '',
            'Balance': '100.00',
        },
        {
            'Transaction Date': '02/01/2020',
            'Transaction Type': 'BGC',
            "Sort Code": "'80-49-57",
            'Account Number': 123,
            'Transaction Description': 'Test Credit',
            'Debit Amount': '',
            'Credit Amount': '50.00',
            'Balance': '150.00',
        },
    ]
    df = pd.DataFrame(data)
    result = bank_extract_clean(df)
    
    # Contract: Intermediate columns are removed
    assert 'DebitAmount' not in result.columns
    assert 'CreditAmount' not in result.columns
    
    # Contract: Result still has expected columns
    assert 'TransactionValue' in result.columns
    assert 'SortCode' in result.columns


def test_bank_extract_clean_computes_transaction_value():
    """Test that TransactionValue = CreditAmount - DebitAmount."""
    data = [
        {
            'Transaction Date': '01/01/2020',
            'Debit Amount': '10.50',
            'Credit Amount': '',
            'Balance': '100.00',
        },
        {
            'Transaction Date': '02/01/2020',
            'Debit Amount': '',
            'Credit Amount': '50.00',
            'Balance': '150.00',
        },
    ]
    df = pd.DataFrame(data)
    result = bank_extract_clean(df)
    
    # Contract: TransactionValue = Credit - Debit
    assert 'TransactionValue' in result.columns
    expected_values = [0.0 - 10.5, 50.0 - 0.0]
    actual_values = result['TransactionValue'].tolist()
    assert actual_values == expected_values, f"Expected {expected_values}, got {actual_values}"


def test_bank_extract_clean_cleans_sort_code():
    """Test that SortCode apostrophe is removed."""
    data = [
        {
            'Transaction Date': '01/01/2020',
            "Sort Code": "'80-49-57",
            'Debit Amount': '10.50',
            'Credit Amount': '',
            'Balance': '100.00',
        }
    ]
    df = pd.DataFrame(data)
    result = bank_extract_clean(df)
    
    # Contract: Leading apostrophe removed from sort code
    assert result.loc[0, 'SortCode'] == '80-49-57'

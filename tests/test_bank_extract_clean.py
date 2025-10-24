import pandas as pd
from analyzer.workflows.bank_extract_clean import bank_extract_clean


def test_bank_extract_clean_basic():
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
    out = bank_extract_clean(df)
    # SortCode apostrophe removed
    assert out.loc[0, 'SortCode'] == '80-49-57'
    # Debit and credit columns dropped
    assert 'DebitAmount' not in out.columns
    assert 'CreditAmount' not in out.columns
    # TransactionValue computed as credit - debit
    assert out.loc[0, 'TransactionValue'] == 0.0 - 10.5
    assert out.loc[1, 'TransactionValue'] == 50.0

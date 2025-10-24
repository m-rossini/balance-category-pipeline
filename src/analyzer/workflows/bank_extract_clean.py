import pandas as pd

def create_transaction_number(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a unique transaction number column to the DataFrame.
    The transaction number is generated in reverse order, starting from the total number of rows down to 1.
    """
    df = df.reset_index(drop=True)  # Ensure the index is reset before assigning transaction numbers
    df['TransactionNumber'] = len(df) - df.index  # Generate transaction numbers in reverse order
    return df

def bank_extract_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Add transaction number column
    df = create_transaction_number(df)

    # Remove spaces from all column names
    df.columns = [col.replace(' ', '') for col in df.columns]
    # Remove the character ' from SortCode
    if 'SortCode' in df.columns:
        df['SortCode'] = df['SortCode'].astype(str).str.replace("'",
                                                                "",
                                                                regex=False)
    if 'DebitAmount' in df.columns:
        # sanitize possible thousands separators, parentheses and currency symbols
        df['DebitAmount'] = df['DebitAmount'].astype(str).str.replace(',', '', regex=False).str.replace('(', '-', regex=False).str.replace(')', '', regex=False).str.replace('£', '', regex=False).str.replace('$', '', regex=False).str.strip()
        df['DebitAmount'] = pd.to_numeric(df['DebitAmount'], errors='coerce').fillna(0)
    if 'CreditAmount' in df.columns:
        df['CreditAmount'] = df['CreditAmount'].astype(str).str.replace(',', '', regex=False).str.replace('(', '-', regex=False).str.replace(')', '', regex=False).str.replace('£', '', regex=False).str.replace('$', '', regex=False).str.strip()
        df['CreditAmount'] = pd.to_numeric(df['CreditAmount'], errors='coerce').fillna(0)
    if 'Balance' in df.columns:
        df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
    # Create a single TransactionValue column (credit - debit).
    # Use 0 for missing columns so we always compute a numeric TransactionValue when possible.
    credit_series = df['CreditAmount'] if 'CreditAmount' in df.columns else 0
    debit_series = df['DebitAmount'] if 'DebitAmount' in df.columns else 0
    try:
        df['TransactionValue'] = credit_series - debit_series
    except Exception:
        # Fallback: coerce both to numeric scalars/series. If scalars, convert to Series to allow fillna.
        if not hasattr(credit_series, 'fillna'):
            credit_series = pd.Series([credit_series] * len(df), index=df.index)
        if not hasattr(debit_series, 'fillna'):
            debit_series = pd.Series([debit_series] * len(df), index=df.index)
        df['TransactionValue'] = pd.to_numeric(credit_series, errors='coerce').fillna(0) - pd.to_numeric(debit_series, errors='coerce').fillna(0)
    # Add annotation column if missing
    if 'CategoryAnnotation' not in df.columns:
        df['CategoryAnnotation'] = ''
    if 'SubCategoryAnnotation' not in df.columns:
        df['SubCategoryAnnotation'] = ''
    if 'Confidence' not in df.columns:
        df['Confidence'] = ''
    # Drop DebitAmount and CreditAmount columns if present
    for col in ['DebitAmount', 'CreditAmount']:
        if col in df.columns:
            df = df.drop(columns=[col])
    df = df.dropna(how='all')
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()
    df = df.reset_index(drop=True)
    return df
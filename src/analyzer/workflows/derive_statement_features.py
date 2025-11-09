import pandas as pd

def derive_statement_features(df: pd.DataFrame) -> pd.DataFrame:
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
    df['Year'] = df['TransactionDate'].dt.year
    df['Month'] = df['TransactionDate'].dt.month
    df['Day'] = df['TransactionDate'].dt.day
    df['DayOfWeek'] = df['TransactionDate'].dt.dayofweek
    df['WeekOfYear'] = df['TransactionDate'].dt.isocalendar().week
    df['WeekOfMonth'] = ((df['TransactionDate'].dt.day - 1) // 7) + 1
    df['Quarter'] = df['TransactionDate'].dt.quarter
    df['Semester'] = ((df['TransactionDate'].dt.month - 1) // 6) + 1
    df['IsWeekend'] = df['TransactionDate'].dt.dayofweek >= 5

    # Sort by date descending to ensure proper running calculations
    df_sorted = df.sort_values('TransactionDate', ascending=False)
    
    # Overall running calculations (descending order)
    df['RunningSum'] = df_sorted['Amount'].cumsum()
    df['RunningCount'] = range(1, len(df_sorted) + 1)
    df['RunningAverage'] = df['RunningSum'] / df['RunningCount']
    
    # Running calculations per year
    df['RunningSumYear'] = df_sorted.groupby('Year')['Amount'].cumsum()
    df['RunningCountYear'] = df_sorted.groupby('Year').cumcount() + 1
    df['RunningAverageYear'] = df['RunningSumYear'] / df['RunningCountYear']
    
    # Running calculations per month
    df['RunningSumMonth'] = df_sorted.groupby(['Year', 'Month'])['Amount'].cumsum()
    df['RunningCountMonth'] = df_sorted.groupby(['Year', 'Month']).cumcount() + 1
    df['RunningAverageMonth'] = df['RunningSumMonth'] / df['RunningCountMonth']
    # Value binning
    bins = [0, 10, 50, 150, 500, 1500, 999999]
    labels = ['0-10', '10.01-50', '50.01-150', '150.01-500', '500.01-1500', '1500+']
    df['AmountBin'] = pd.cut(df['Amount'], bins=bins, labels=labels, include_lowest=True)
    return df

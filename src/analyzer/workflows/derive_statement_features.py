import pandas as pd

def derive_statement_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        # Handle empty dataframe case
        df = df.copy()
        df['TransactionDate'] = pd.to_datetime(df.get('TransactionDate', pd.Series([], dtype='datetime64[ns]')))
        df['Year'] = pd.Series([], dtype='Int64')
        df['Month'] = pd.Series([], dtype='Int64')
        df['Day'] = pd.Series([], dtype='Int64')
        df['DayOfWeek'] = pd.Series([], dtype='Int64')
        df['WeekOfYear'] = pd.Series([], dtype='UInt32')
        df['WeekOfMonth'] = pd.Series([], dtype='Int64')
        df['Quarter'] = pd.Series([], dtype='Int64')
        df['Semester'] = pd.Series([], dtype='Int64')
        df['IsWeekend'] = pd.Series([], dtype='boolean')
        df['RunningSum'] = pd.Series([], dtype='float64')
        df['RunningCount'] = pd.Series([], dtype='Int64')
        df['RunningAverage'] = pd.Series([], dtype='float64')
        df['RunningSumYear'] = pd.Series([], dtype='float64')
        df['RunningCountYear'] = pd.Series([], dtype='Int64')
        df['RunningAverageYear'] = pd.Series([], dtype='float64')
        df['RunningSumMonth'] = pd.Series([], dtype='float64')
        df['RunningCountMonth'] = pd.Series([], dtype='Int64')
        df['RunningAverageMonth'] = pd.Series([], dtype='float64')
        df['TransactionValueBin'] = pd.Categorical([], categories=['0-10', '10.01-50', '50.01-150', '150.01-500', '500.01-1500', '1500+'])
        return df
    
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], dayfirst=True, errors='coerce')
    df['Year'] = df['TransactionDate'].dt.year
    df['Month'] = df['TransactionDate'].dt.month
    df['Day'] = df['TransactionDate'].dt.day
    df['DayOfWeek'] = df['TransactionDate'].dt.dayofweek
    df['WeekOfYear'] = df['TransactionDate'].dt.isocalendar().week
    df['WeekOfMonth'] = ((df['TransactionDate'].dt.day - 1) // 7) + 1
    df['Quarter'] = df['TransactionDate'].dt.quarter
    df['Semester'] = ((df['TransactionDate'].dt.month - 1) // 6) + 1
    df['IsWeekend'] = df['TransactionDate'].dt.dayofweek >= 5

    df_temp = df.copy()
    df_ascending = df_temp.sort_values('TransactionDate', ascending=True)
    df_ascending['RunningSum'] = df_ascending['TransactionValue'].cumsum()
    df_ascending['RunningCount'] = range(1, len(df_ascending) + 1)
    df_ascending['RunningAverage'] = df_ascending['RunningSum'] / df_ascending['RunningCount']
    
    # Map running calculations back to original order using TransactionDate as key
    running_overall = df_ascending.set_index('TransactionDate')[['RunningSum', 'RunningCount', 'RunningAverage']]
    df = df.merge(running_overall, left_on='TransactionDate', right_index=True, how='left')
    
    # Running calculations per year (chronological within each year)
    df_year_temp = df.copy()
    df_year_ascending = df_year_temp.sort_values(['Year', 'TransactionDate'], ascending=[True, True])
    df_year_ascending['RunningSumYear'] = df_year_ascending.groupby('Year')['TransactionValue'].cumsum()
    df_year_ascending['RunningCountYear'] = df_year_ascending.groupby('Year').cumcount() + 1
    df_year_ascending['RunningAverageYear'] = df_year_ascending['RunningSumYear'] / df_year_ascending['RunningCountYear']
    
    # Map yearly running calculations back
    running_yearly = df_year_ascending.set_index('TransactionDate')[['RunningSumYear', 'RunningCountYear', 'RunningAverageYear']]
    df = df.merge(running_yearly, left_on='TransactionDate', right_index=True, how='left')
    
    # Running calculations per month (chronological within each month)
    df_month_temp = df.copy()
    df_month_ascending = df_month_temp.sort_values(['Year', 'Month', 'TransactionDate'], ascending=[True, True, True])
    df_month_ascending['RunningSumMonth'] = df_month_ascending.groupby(['Year', 'Month'])['TransactionValue'].cumsum()
    df_month_ascending['RunningCountMonth'] = df_month_ascending.groupby(['Year', 'Month']).cumcount() + 1
    df_month_ascending['RunningAverageMonth'] = df_month_ascending['RunningSumMonth'] / df_month_ascending['RunningCountMonth']
    
    # Map monthly running calculations back
    running_monthly = df_month_ascending.set_index('TransactionDate')[['RunningSumMonth', 'RunningCountMonth', 'RunningAverageMonth']]
    df = df.merge(running_monthly, left_on='TransactionDate', right_index=True, how='left')
    # Value binning
    bins = [0, 10, 50, 150, 500, 1500, 999999]
    labels = ['0-10', '10.01-50', '50.01-150', '150.01-500', '500.01-1500', '1500+']
    df['TransactionValueBin'] = pd.cut(df['TransactionValue'], bins=bins, labels=labels, include_lowest=True)
    
    # Return dataframe in original order (assumed to be descending date order)
    return df

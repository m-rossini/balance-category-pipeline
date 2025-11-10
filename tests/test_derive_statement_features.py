import pandas as pd
from analyzer.workflows.derive_statement_features import derive_statement_features


def test_derive_statement_features_creates_date_features():
    """Test that derive_statement_features creates all expected date features."""
    data = [
        {
            'TransactionDate': '25/12/2023',  # Monday (weekday 0) - newest
            'TransactionValue': 300.0,
        },
        {
            'TransactionDate': '25/07/2023',  # Tuesday (weekday 1)
            'TransactionValue': 200.0,
        },
        {
            'TransactionDate': '15/01/2023',  # Sunday (weekday 6) - oldest
            'TransactionValue': 100.0,
        },
    ]
    df = pd.DataFrame(data)
    result = derive_statement_features(df)
    expected_columns = [
        'Year', 'Month', 'Day', 'DayOfWeek', 'WeekOfYear',
        'WeekOfMonth', 'Quarter', 'Semester', 'IsWeekend'
    ]
    for col in expected_columns:
        assert col in result.columns, f"Missing column: {col}"

    assert result.loc[0, 'Year'] == 2023
    assert result.loc[0, 'Month'] == 12
    assert result.loc[0, 'Day'] == 25
    assert result.loc[0, 'DayOfWeek'] == 0  # Monday
    assert result.loc[0, 'WeekOfYear'] == 52  # Week 52 of 2023
    assert result.loc[0, 'WeekOfMonth'] == 4  # Fourth week of December
    assert result.loc[0, 'Quarter'] == 4
    assert result.loc[0, 'Semester'] == 2
    assert result.loc[0, 'IsWeekend'] == False

    assert result.loc[1, 'Year'] == 2023
    assert result.loc[1, 'Month'] == 7
    assert result.loc[1, 'Day'] == 25
    assert result.loc[1, 'DayOfWeek'] == 1  # Tuesday
    assert result.loc[1, 'WeekOfYear'] == 30  # Week 30 of 2023
    assert result.loc[1, 'WeekOfMonth'] == 4  # Fourth week of July
    assert result.loc[1, 'Quarter'] == 3
    assert result.loc[1, 'Semester'] == 2
    assert result.loc[1, 'IsWeekend'] == False

    assert result.loc[2, 'Year'] == 2023
    assert result.loc[2, 'Month'] == 1
    assert result.loc[2, 'Day'] == 15
    assert result.loc[2, 'DayOfWeek'] == 6  # Sunday
    assert result.loc[2, 'WeekOfYear'] == 2  # Week 2 of 2023
    assert result.loc[2, 'WeekOfMonth'] == 3  # Third week of January
    assert result.loc[2, 'Quarter'] == 1
    assert result.loc[2, 'Semester'] == 1
    assert result.loc[2, 'IsWeekend'] == True


def test_derive_statement_features_overall_running_calculations():
    """Test that overall running calculations work correctly."""
    data = [
        {'TransactionDate': '25/01/2023', 'TransactionValue': 300.0},  
        {'TransactionDate': '24/01/2023', 'TransactionValue': 200.0},
        {'TransactionDate': '23/01/2023', 'TransactionValue': 100.0},
    ]
    df = pd.DataFrame(data)
    result = derive_statement_features(df)

    assert 'RunningSum' in result.columns
    assert 'RunningCount' in result.columns
    assert 'RunningAverage' in result.columns

    assert result.loc[0, 'RunningSum'] == 600.0  # Just 300
    assert result.loc[0, 'RunningCount'] == 3
    assert result.loc[0, 'RunningAverage'] == 200.0

    assert result.loc[1, 'RunningSum'] == 300.0  # 300 + 200
    assert result.loc[1, 'RunningCount'] == 2
    assert result.loc[1, 'RunningAverage'] == 150.0

    assert result.loc[2, 'RunningSum'] == 100.0  # 300 + 200 + 100
    assert result.loc[2, 'RunningCount'] == 1
    assert result.loc[2, 'RunningAverage'] == 100.0


    """Test that yearly running calculations work correctly."""
    data = [
        {'TransactionDate': '25/01/2024', 'TransactionValue': 150.0},  # 2024 - newest
        {'TransactionDate': '24/01/2023', 'TransactionValue': 200.0},  # 2023
        {'TransactionDate': '23/01/2023', 'TransactionValue': 100.0},  # 2023
        {'TransactionDate': '22/12/2022', 'TransactionValue': 50.0},   # 2022 - oldest
    ]
    df = pd.DataFrame(data)
    result = derive_statement_features(df)

    assert 'RunningSumYear' in result.columns
    assert 'RunningCountYear' in result.columns
    assert 'RunningAverageYear' in result.columns

    year_2024 = result[result['Year'] == 2024].iloc[0]
    assert year_2024['RunningSumYear'] == 150.0
    assert year_2024['RunningCountYear'] == 1
    assert year_2024['RunningAverageYear'] == 150.0

    year_2023_rows = result[result['Year'] == 2023].sort_values('TransactionDate', ascending=False)
    assert year_2023_rows.iloc[0]['RunningSumYear'] == 300.0  
    assert year_2023_rows.iloc[0]['RunningCountYear'] == 2
    assert year_2023_rows.iloc[0]['RunningAverageYear'] == 150.0

    assert year_2023_rows.iloc[1]['RunningSumYear'] == 100.0  
    assert year_2023_rows.iloc[1]['RunningCountYear'] == 1
    assert year_2023_rows.iloc[1]['RunningAverageYear'] == 100.0

    year_2022 = result[result['Year'] == 2022].iloc[0]
    assert year_2022['RunningSumYear'] == 50.0
    assert year_2022['RunningCountYear'] == 1
    assert year_2022['RunningAverageYear'] == 50.0


def test_derive_statement_features_monthly_running_calculations():
    """Test that monthly running calculations work correctly."""
    data = [
        {'TransactionDate': '25/02/2023', 'TransactionValue': 150.0},  
        {'TransactionDate': '24/01/2023', 'TransactionValue': 200.0},  
        {'TransactionDate': '23/01/2023', 'TransactionValue': 100.0}, 
    ]
    df = pd.DataFrame(data)
    
    result = derive_statement_features(df)

    assert 'RunningSumMonth' in result.columns
    assert 'RunningCountMonth' in result.columns
    assert 'RunningAverageMonth' in result.columns

    jan_rows = result[(result['Year'] == 2023) & (result['Month'] == 1)].sort_values('TransactionDate', ascending=False)
    assert jan_rows.iloc[0]['RunningSumMonth'] == 300.0  
    assert jan_rows.iloc[0]['RunningCountMonth'] == 2
    assert jan_rows.iloc[0]['RunningAverageMonth'] == 150.0

    assert jan_rows.iloc[1]['RunningSumMonth'] == 100.0  
    assert jan_rows.iloc[1]['RunningCountMonth'] == 1
    assert jan_rows.iloc[1]['RunningAverageMonth'] == 100.0

    feb_row = result[(result['Year'] == 2023) & (result['Month'] == 2)].iloc[0]
    assert feb_row['RunningSumMonth'] == 150.0
    assert feb_row['RunningCountMonth'] == 1
    assert feb_row['RunningAverageMonth'] == 150.0


def test_derive_statement_features_TransactionValue_binning():
    """Test that TransactionValue binning works correctly."""
    data = [
        {'TransactionDate': '30/01/2023', 'TransactionValue': 2000.0},  # 1500+ - newest
        {'TransactionDate': '29/01/2023', 'TransactionValue': 1000.0},  # 500.01-1500
        {'TransactionDate': '28/01/2023', 'TransactionValue': 300.0},   # 150.01-500
        {'TransactionDate': '27/01/2023', 'TransactionValue': 100.0},   # 50.01-150
        {'TransactionDate': '26/01/2023', 'TransactionValue': 25.0},    # 10.01-50
        {'TransactionDate': '25/01/2023', 'TransactionValue': 5.0},     # 0-10 - oldest
    ]
    df = pd.DataFrame(data)
    result = derive_statement_features(df)

    assert 'TransactionValueBin' in result.columns

    expected_bins = ['1500+', '500.01-1500', '150.01-500', '50.01-150', '10.01-50', '0-10']
    actual_bins = result['TransactionValueBin'].tolist()

    assert actual_bins == expected_bins


def test_derive_statement_features_preserves_original_columns():
    """Test that original columns are preserved."""
    data = [
        {
            'TransactionDate': '25/01/2023',
            'TransactionValue': 100.0,
            'Description': 'Test transaction',
            'Category': 'Food',
        }
    ]
    df = pd.DataFrame(data)
    print("DataFrame before derive_statement_features:")
    print(df)
    print()
    
    result = derive_statement_features(df)

    assert 'TransactionDate' in result.columns
    assert 'TransactionValue' in result.columns
    assert 'Description' in result.columns
    assert 'Category' in result.columns

    assert result.loc[0, 'TransactionValue'] == 100.0
    assert result.loc[0, 'Description'] == 'Test transaction'
    assert result.loc[0, 'Category'] == 'Food'


def test_derive_statement_features_empty_dataframe():
    """Test that function handles empty DataFrame gracefully."""
    df = pd.DataFrame(columns=['TransactionDate', 'TransactionValue'])
    result = derive_statement_features(df)
    
    expected_columns = [
        'TransactionDate', 'TransactionValue', 'Year', 'Month', 'Day', 'DayOfWeek',
        'WeekOfYear', 'WeekOfMonth', 'Quarter', 'Semester', 'IsWeekend',
        'RunningSum', 'RunningCount', 'RunningAverage',
        'RunningSumYear', 'RunningCountYear', 'RunningAverageYear',
        'RunningSumMonth', 'RunningCountMonth', 'RunningAverageMonth',
        'TransactionValueBin'
    ]

    for col in expected_columns:
        assert col in result.columns, f"Missing column: {col}"

    assert len(result) == 0


def test_derive_statement_features_single_row():
    """Test that function works with single row DataFrame."""
    data = [{'TransactionDate': '25/06/2023', 'TransactionValue': 75.0}]
    df = pd.DataFrame(data)
    print("DataFrame before derive_statement_features:")
    print(df)
    print()
    
    result = derive_statement_features(df)

    # Contract: Single row calculations work
    assert result.loc[0, 'RunningSum'] == 75.0
    assert result.loc[0, 'RunningCount'] == 1
    assert result.loc[0, 'RunningAverage'] == 75.0

    # Contract: Yearly/monthly calculations work for single row
    assert result.loc[0, 'RunningSumYear'] == 75.0
    assert result.loc[0, 'RunningCountYear'] == 1
    assert result.loc[0, 'RunningAverageYear'] == 75.0

    assert result.loc[0, 'RunningSumMonth'] == 75.0
    assert result.loc[0, 'RunningCountMonth'] == 1
    assert result.loc[0, 'RunningAverageMonth'] == 75.0

    # Contract: TransactionValue binning works
    assert result.loc[0, 'TransactionValueBin'] == '50.01-150'
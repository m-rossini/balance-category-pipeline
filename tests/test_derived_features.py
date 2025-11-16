import pandas as pd
import pytest
from analyzer.workflows.derive_statement_features import derive_statement_features


@pytest.fixture
def comprehensive_test_data():
    """Comprehensive test dataset covering multiple years, months, and scenarios.
    
    Dataset design:
    - 3 years: 2022, 2023, 2024 
    - 4 months: January, March, June, December
    - Multiple transactions per year/month for running calculations
    - Various amounts for binning tests
    - Weekend/weekday mix
    - TransactionNumber follows chronological order (1=oldest, higher=newer)
    """
    data = [
        # 2024 - Most recent year
        {'TransactionDate': '15/12/2024', 'TransactionValue': 2000.0, 'TransactionNumber': 12},  # Saturday, 1500+ bin
        {'TransactionDate': '10/06/2024', 'TransactionValue': 800.0, 'TransactionNumber': 11},   # Monday, 500.01-1500 bin
        {'TransactionDate': '05/03/2024', 'TransactionValue': 250.0, 'TransactionNumber': 10},   # Tuesday, 150.01-500 bin
        {'TransactionDate': '20/01/2024', 'TransactionValue': 75.0, 'TransactionNumber': 9},     # Saturday, 50.01-150 bin
        
        # 2023 - Middle year (multiple per month)  
        {'TransactionDate': '25/12/2023', 'TransactionValue': 300.0, 'TransactionNumber': 8},    # Monday, 150.01-500 bin
        {'TransactionDate': '20/12/2023', 'TransactionValue': 150.0, 'TransactionNumber': 7},    # Wednesday, 150.01-500 bin
        {'TransactionDate': '15/06/2023', 'TransactionValue': 45.0, 'TransactionNumber': 6},     # Thursday, 10.01-50 bin
        {'TransactionDate': '10/06/2023', 'TransactionValue': 25.0, 'TransactionNumber': 5},     # Saturday, 10.01-50 bin
        {'TransactionDate': '05/03/2023', 'TransactionValue': 100.0, 'TransactionNumber': 4},    # Sunday, 50.01-150 bin
        
        # 2022 - Oldest year
        {'TransactionDate': '30/01/2022', 'TransactionValue': 5.0, 'TransactionNumber': 3},      # Sunday, 0-10 bin  
        {'TransactionDate': '25/01/2022', 'TransactionValue': 200.0, 'TransactionNumber': 2},    # Tuesday, 150.01-500 bin
        {'TransactionDate': '01/01/2022', 'TransactionValue': 50.0, 'TransactionNumber': 1},     # Saturday, 50.01-150 bin - OLDEST
    ]
    return pd.DataFrame(data)


def test_feature_year(comprehensive_test_data):
    """Test Year feature extraction from TransactionDate."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify Year column exists
    assert 'Year' in result.columns
    
    # Verify specific year values
    assert result[result['TransactionNumber'] == 1]['Year'].iloc[0] == 2022
    assert result[result['TransactionNumber'] == 4]['Year'].iloc[0] == 2023
    assert result[result['TransactionNumber'] == 9]['Year'].iloc[0] == 2024
    
    # Verify all years are present
    years = sorted(result['Year'].unique())
    assert years == [2022, 2023, 2024]


def test_feature_month(comprehensive_test_data):
    """Test Month feature extraction from TransactionDate."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify Month column exists
    assert 'Month' in result.columns
    
    # Verify specific month values
    assert result[result['TransactionNumber'] == 1]['Month'].iloc[0] == 1  # January
    assert result[result['TransactionNumber'] == 4]['Month'].iloc[0] == 3  # March
    assert result[result['TransactionNumber'] == 5]['Month'].iloc[0] == 6  # June
    assert result[result['TransactionNumber'] == 8]['Month'].iloc[0] == 12  # December
    
    # Verify all expected months are present
    months = sorted(result['Month'].unique())
    assert set(months) == {1, 3, 6, 12}


def test_feature_day(comprehensive_test_data):
    """Test Day feature extraction from TransactionDate."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify Day column exists
    assert 'Day' in result.columns
    
    # Verify specific day values
    assert result[result['TransactionNumber'] == 1]['Day'].iloc[0] == 1    # 01/01/2022
    assert result[result['TransactionNumber'] == 2]['Day'].iloc[0] == 25   # 25/01/2022
    assert result[result['TransactionNumber'] == 12]['Day'].iloc[0] == 15  # 15/12/2024


def test_feature_day_of_week(comprehensive_test_data):
    """Test DayOfWeek feature (0=Monday, 6=Sunday)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify DayOfWeek column exists
    assert 'DayOfWeek' in result.columns
    
    # Verify specific day of week values (manually verified dates)
    txn1_dow = result[result['TransactionNumber'] == 1]['DayOfWeek'].iloc[0]  # 01/01/2022 = Saturday
    assert txn1_dow == 5  # Saturday = 5
    
    txn4_dow = result[result['TransactionNumber'] == 4]['DayOfWeek'].iloc[0]  # 05/03/2023 = Sunday  
    assert txn4_dow == 6  # Sunday = 6
    
    txn11_dow = result[result['TransactionNumber'] == 11]['DayOfWeek'].iloc[0]  # 10/06/2024 = Monday
    assert txn11_dow == 0  # Monday = 0


def test_feature_quarter(comprehensive_test_data):
    """Test Quarter feature (Q1=1-3, Q2=4-6, Q3=7-9, Q4=10-12)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify Quarter column exists
    assert 'Quarter' in result.columns
    
    # Verify quarter assignments
    jan_quarter = result[result['TransactionNumber'] == 1]['Quarter'].iloc[0]  # January
    assert jan_quarter == 1
    
    mar_quarter = result[result['TransactionNumber'] == 4]['Quarter'].iloc[0]  # March
    assert mar_quarter == 1
    
    jun_quarter = result[result['TransactionNumber'] == 5]['Quarter'].iloc[0]  # June
    assert jun_quarter == 2
    
    dec_quarter = result[result['TransactionNumber'] == 8]['Quarter'].iloc[0]  # December
    assert dec_quarter == 4


def test_feature_semester(comprehensive_test_data):
    """Test Semester feature (S1=1-6, S2=7-12)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify Semester column exists
    assert 'Semester' in result.columns
    
    # Verify semester assignments
    jan_semester = result[result['TransactionNumber'] == 1]['Semester'].iloc[0]  # January
    assert jan_semester == 1
    
    jun_semester = result[result['TransactionNumber'] == 5]['Semester'].iloc[0]  # June
    assert jun_semester == 1
    
    dec_semester = result[result['TransactionNumber'] == 8]['Semester'].iloc[0]  # December
    assert dec_semester == 2


def test_feature_is_weekend(comprehensive_test_data):
    """Test IsWeekend feature (True for Friday/Saturday)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify IsWeekend column exists
    assert 'IsWeekend' in result.columns
    
    # Verify weekend detection
    txn1_weekend = result[result['TransactionNumber'] == 1]['IsWeekend'].iloc[0]  # Saturday
    assert txn1_weekend == True
    
    txn4_weekend = result[result['TransactionNumber'] == 4]['IsWeekend'].iloc[0]  # Sunday
    assert txn4_weekend == True
    
    txn11_weekend = result[result['TransactionNumber'] == 11]['IsWeekend'].iloc[0]  # Monday
    assert txn11_weekend == False


def test_feature_running_sum_overall(comprehensive_test_data):
    """Test RunningSum feature (cumulative sum by TransactionNumber order)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify RunningSum column exists
    assert 'RunningSum' in result.columns
    
    # Sort by TransactionNumber to verify cumulative calculation
    sorted_result = result.sort_values('TransactionNumber')
    
    # Verify cumulative sum calculation
    # TxnNum 1: 50.0 -> RunningSum = 50.0
    assert sorted_result.iloc[0]['RunningSum'] == 50.0
    
    # TxnNum 2: 50.0 + 200.0 -> RunningSum = 250.0
    assert sorted_result.iloc[1]['RunningSum'] == 250.0
    
    # TxnNum 3: 250.0 + 5.0 -> RunningSum = 255.0
    assert sorted_result.iloc[2]['RunningSum'] == 255.0
    
    # Final transaction should have sum of all values
    final_sum = sorted_result.iloc[-1]['RunningSum']
    expected_total = comprehensive_test_data['TransactionValue'].sum()
    assert final_sum == expected_total


def test_feature_running_count_overall(comprehensive_test_data):
    """Test RunningCount feature (running count by TransactionNumber order)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify RunningCount column exists
    assert 'RunningCount' in result.columns
    
    # Sort by TransactionNumber to verify running count
    sorted_result = result.sort_values('TransactionNumber')
    
    # Verify running count is sequential
    for i, row in enumerate(sorted_result.itertuples(), 1):
        assert row.RunningCount == i
    
    # Verify that the running count equals the TransactionNumber for this dataset
    for _, row in result.iterrows():
        assert row['RunningCount'] == row['TransactionNumber']


def test_feature_running_sum_year(comprehensive_test_data):
    """Test RunningSumYear feature (cumulative sum within each year)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify RunningSumYear column exists
    assert 'RunningSumYear' in result.columns
    
    # Test 2022: TxnNum 1 (50.0), TxnNum 2 (200.0), TxnNum 3 (5.0)
    year_2022 = result[result['Year'] == 2022].sort_values('TransactionNumber')
    assert year_2022.iloc[0]['RunningSumYear'] == 50.0    # First in 2022
    assert year_2022.iloc[1]['RunningSumYear'] == 250.0   # 50 + 200
    assert year_2022.iloc[2]['RunningSumYear'] == 255.0   # 50 + 200 + 5
    
    # Test 2023: Should restart cumulative sum
    year_2023 = result[result['Year'] == 2023].sort_values('TransactionNumber')
    first_2023_sum = year_2023.iloc[0]['RunningSumYear']
    assert first_2023_sum == 100.0  # First transaction in 2023 (TxnNum 4)


def test_feature_running_count_month(comprehensive_test_data):
    """Test RunningCountMonth feature (running count within each year-month)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify RunningCountMonth column exists
    assert 'RunningCountMonth' in result.columns
    
    # Test December 2023: Has 2 transactions (TxnNum 7, 8)
    dec_2023 = result[(result['Year'] == 2023) & (result['Month'] == 12)].sort_values('TransactionNumber')
    assert len(dec_2023) == 2
    assert dec_2023.iloc[0]['RunningCountMonth'] == 1  # First in month
    assert dec_2023.iloc[1]['RunningCountMonth'] == 2  # Second in month
    
    # Test June 2023: Has 2 transactions (TxnNum 5, 6)
    jun_2023 = result[(result['Year'] == 2023) & (result['Month'] == 6)].sort_values('TransactionNumber')
    assert len(jun_2023) == 2
    assert jun_2023.iloc[0]['RunningCountMonth'] == 1  # First in month
    assert jun_2023.iloc[1]['RunningCountMonth'] == 2  # Second in month


def test_feature_transaction_value_bin(comprehensive_test_data):
    """Test TransactionValueBin feature (categorical bins for amounts)."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify TransactionValueBin column exists
    assert 'TransactionValueBin' in result.columns
    
    # Test specific binning (boundaries: 0, 10, 50, 150, 500, 1500, 999999)
    txn1_bin = result[result['TransactionNumber'] == 1]['TransactionValueBin'].iloc[0]  # 50.0
    assert txn1_bin == '10.01-50'  # 50.0 exactly on boundary goes to lower bin
    
    txn3_bin = result[result['TransactionNumber'] == 3]['TransactionValueBin'].iloc[0]  # 5.0  
    assert txn3_bin == '0-10'
    
    txn12_bin = result[result['TransactionNumber'] == 12]['TransactionValueBin'].iloc[0]  # 2000.0
    assert txn12_bin == '1500+'
    
    # Test a few more specific values
    txn10_bin = result[result['TransactionNumber'] == 10]['TransactionValueBin'].iloc[0]  # 250.0
    assert txn10_bin == '150.01-500'
    
    # Verify all expected bins are present
    bins = result['TransactionValueBin'].cat.categories.tolist()
    expected_bins = ['0-10', '10.01-50', '50.01-150', '150.01-500', '500.01-1500', '1500+']
    assert bins == expected_bins


def test_feature_running_average_calculations(comprehensive_test_data):
    """Test all running average features are calculated correctly."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Test overall running average
    sorted_result = result.sort_values('TransactionNumber')
    for _, row in sorted_result.iterrows():
        expected_avg = row['RunningSum'] / row['RunningCount']
        assert abs(row['RunningAverage'] - expected_avg) < 0.01  # Allow small floating point error
    
    # Test yearly running average
    for _, row in result.iterrows():
        expected_avg = row['RunningSumYear'] / row['RunningCountYear']
        assert abs(row['RunningAverageYear'] - expected_avg) < 0.01
    
    # Test monthly running average  
    for _, row in result.iterrows():
        expected_avg = row['RunningSumMonth'] / row['RunningCountMonth']
        assert abs(row['RunningAverageMonth'] - expected_avg) < 0.01


def test_row_count_preservation(comprehensive_test_data):
    """Test that derive_statement_features preserves row count (critical integrity check)."""
    input_rows = len(comprehensive_test_data)
    result = derive_statement_features(comprehensive_test_data)
    output_rows = len(result)
    
    assert input_rows == output_rows, f"Row count changed! Input: {input_rows}, Output: {output_rows}"


def test_original_columns_preserved(comprehensive_test_data):
    """Test that original columns are preserved alongside new features."""
    result = derive_statement_features(comprehensive_test_data)
    
    # Verify original columns still exist
    for col in comprehensive_test_data.columns:
        assert col in result.columns, f"Original column {col} was lost"
    
    # Verify original data is unchanged
    for col in ['TransactionNumber', 'TransactionValue']:
        original_values = comprehensive_test_data[col].tolist()
        result_values = result[col].tolist()
        assert original_values == result_values, f"Original data in {col} was modified"


def test_all_expected_features_present(comprehensive_test_data):
    """Test that all expected feature columns are created."""
    result = derive_statement_features(comprehensive_test_data)
    
    expected_features = [
        'Year', 'Month', 'Day', 'DayOfWeek', 'WeekOfYear', 'WeekOfMonth',
        'Quarter', 'Semester', 'IsWeekend',
        'RunningSum', 'RunningCount', 'RunningAverage', 
        'RunningSumYear', 'RunningCountYear', 'RunningAverageYear',
        'RunningSumMonth', 'RunningCountMonth', 'RunningAverageMonth',
        'TransactionValueBin'
    ]
    
    for feature in expected_features:
        assert feature in result.columns, f"Expected feature {feature} not found"
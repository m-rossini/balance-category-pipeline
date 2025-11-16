"""Test suite for simulating pipeline configurations."""
import pytest
import pandas as pd
from tempfile import TemporaryDirectory
from pathlib import Path
from analyzer.pipeline.pipeline_commands import DataPipeline, AppendFilesCommand, SaveFileCommand
from analyzer.pipeline.metadata import MetadataCollector


def build_transactions_for_year(year: int) -> pd.DataFrame:
    """Return a DataFrame with realistic transactions for the requested year.

    The data mirrors the content previously inlined in the test and is kept
    stable here to be reused across tests.
    """
    datasets = {}
    datasets[2023] = {
        "Transaction Date": [
            "28/12/2023", "20/12/2023", "15/12/2023",
            "25/11/2023", "10/11/2023",
            "28/10/2023", "15/10/2023", "03/10/2023",
            "20/09/2023", "08/09/2023",
            "30/08/2023", "18/08/2023", "05/08/2023",
            "22/07/2023", "10/07/2023",
            "25/06/2023", "15/06/2023", "12/06/2023",
            "20/05/2023", "08/05/2023",
            "28/04/2023", "18/04/2023", "05/04/2023",
            "22/03/2023", "10/03/2023",
            "18/02/2023", "05/02/2023",
            "30/01/2023", "25/01/2023", "12/01/2023",
        ],
        "Transaction Type": [
            "DEB", "DEB", "DD",
            "DEB", "DD",
            "BGC", "DEB", "DD",
            "DD", "DEB",
            "BGC", "DEB", "DEB",
            "DEB", "DD",
            "DEB", "FPO", "BGC",
            "DD", "DEB",
            "DEB", "FPI", "DD",
            "DEB", "DD",
            "DD", "DEB",
            "DEB", "DEB", "BGC",
        ],
        "Sort Code": ["'80-49-57"] * 30,
        "Account Number": ["12343960"] * 30,
        "Transaction Description": [
            "Grocery Store", "Amazon.com", "Internet Bill",
            "Restaurant", "Phone Bill",
            "BLOOM LP WAGES", "Coffee Shop", "Council Tax",
            "Electricity Bill", "Gas Station",
            "BLOOM LP WAGES", "Pharmacy", "Supermarket",
            "Shopping Mall", "Water Bill",
            "Clothing Store", "NARISTER OLIVEIRA", "BLOOM LP WAGES",
            "Insurance", "Bookstore",
            "Hardware Store", "Freelance Payment", "TV Licence",
            "Online Store", "Gas Bill",
            "Cable TV", "Coffee Subscription",
            "Department Store", "Gym Membership", "BLOOM LP WAGES",
        ],
        "Debit Amount": [
            125.50, 89.99, 55.00, 65.30, 45.00, "", 4.75, 244.00,
            85.00, 60.00, "", 28.90, 95.20, 150.00, 35.00,
            120.00, 2000.00, "", 42.50, 88.75, "", 15.00,
            75.50, 50.00, 70.00, 12.99, 200.00, 45.00, "", ""
        ],
        "Credit Amount": [
            "", "", "", "", "", 3200.00, "", "", "", "",
            3200.00, "", "", "", "", "", "", 3200.00, "", "",
            2500.00, "", "", "", "", "", "", "", "", 3200.00
        ],
        "Balance": [
            9083.40, 8993.41, 8938.41, 8873.11, 8828.11, 12028.11,
            12023.36, 11779.36, 11694.36, 11634.36, 14834.36, 14805.46,
            14710.26, 14560.26, 14525.26, 14405.26, 12405.26, 15605.26,
            15562.76, 15474.01, 17974.01, 17959.01, 17883.51, 17833.51,
            17763.51, 17750.52, 17550.52, 17505.52, 17505.52, 20705.52
        ]
    }
    datasets[2024] = {
        "Transaction Date": [
            "30/12/2024", "28/12/2024", "18/12/2024",
            "25/11/2024", "12/11/2024",
            "30/10/2024", "28/10/2024", "15/10/2024",
            "22/09/2024", "10/09/2024",
            "30/08/2024", "20/08/2024", "07/08/2024",
            "25/07/2024", "12/07/2024",
            "30/06/2024", "28/06/2024", "15/06/2024",
            "22/05/2024", "10/05/2024",
            "30/04/2024", "20/04/2024", "07/04/2024",
            "25/03/2024", "12/03/2024",
            "20/02/2024", "07/02/2024",
            "30/01/2024", "28/01/2024", "15/01/2024",
        ],
        "Transaction Type": [
            "BGC", "DEB", "DD",
            "DD", "DEB",
            "DEB", "FPI", "DD",
            "DEB", "DD",
            "BGC", "DEB", "DEB",
            "DEB", "DD",
            "BGC", "DEB", "FPI",
            "DD", "DEB",
            "DEB", "BGC", "FPO",
            "DEB", "DD",
            "DEB", "DD",
            "DEB", "BGC", "DEB",
        ],
        "Sort Code": ["'80-49-57"] * 30,
        "Account Number": ["12343960"] * 30,
        "Transaction Description": [
            "BLOOM LP WAGES", "Electronics Store", "Streaming Service",
            "Council Tax", "Pet Store",
            "Restaurant Chain", "Consulting Fee", "Insurance",
            "Auto Parts", "Phone Bill",
            "BLOOM LP WAGES", "Home Improvement", "Bakery",
            "Furniture Store", "HOA Fee",
            "BLOOM LP WAGES", "Sporting Goods", "Client Payment",
            "Property Tax", "Convenience Store",
            "Garden Center", "BLOOM LP WAGES", "PEDRO PEREZ SERAPI",
            "Car Repair", "Car Insurance",
            "Drugstore", "Medical Bill",
            "Online Shopping", "BLOOM LP WAGES", "Supermarket",
        ],
        "Debit Amount": [
            "", 580.00, 15.99, 244.00, 45.60, 78.40, "", 125.00,
            92.50, 11.90, "", 310.00, 12.50, 165.00, 250.00,
            "", 165.75, "", 450.00, 18.30, 92.80, "", 500.00,
            385.00, 180.00, 32.45, 95.00, 125.50, "", 890.00
        ],
        "Credit Amount": [
            9016.21, "", "", "", "", "", 1800.00, "", "", "",
            9016.21, "", "", "", "", 9016.21, "", 2200.00, "", "",
            "", 9016.21, "", "", "", "", "", "", 9016.21, ""
        ],
        "Balance": [
            18420.00, 17840.00, 17824.01, 17580.01, 17534.41, 17456.01,
            19256.01, 19131.01, 19038.51, 19026.61, 28042.82, 27732.82,
            27720.32, 27555.32, 27305.32, 36321.53, 36155.78, 38355.78,
            37905.78, 37887.48, 37794.68, 46810.89, 46310.89, 45925.89,
            45745.89, 45713.44, 45618.44, 45492.94, 54509.15, 53619.15
        ]
    }
    datasets[2025] = {
        "Transaction Date": [
            "30/12/2025", "29/12/2025", "16/12/2025",
            "24/11/2025", "11/11/2025",
            "30/10/2025", "27/10/2025", "14/10/2025",
            "21/09/2025", "09/09/2025",
            "30/08/2025", "19/08/2025", "06/08/2025",
            "24/07/2025", "11/07/2025",
            "30/06/2025", "27/06/2025", "14/06/2025",
            "21/05/2025", "09/05/2025",
            "30/04/2025", "19/04/2025", "06/04/2025",
            "24/03/2025", "11/03/2025",
            "19/02/2025", "06/02/2025",
            "31/01/2025", "27/01/2025", "14/01/2025",
        ],
        "Transaction Type": [
            "BGC", "DEB", "DD",
            "DEB", "DD",
            "FPI", "DEB", "DD",
            "DEB", "DD",
            "BGC", "DEB", "FPO",
            "DD", "DEB",
            "BGC", "DEB", "FPI",
            "DEB", "DD",
            "BGC", "DEB", "FPO",
            "DEB", "DD",
            "DEB", "DD",
            "BGC", "DEB", "DEB",
        ],
        "Sort Code": ["'80-49-57"] * 30,
        "Account Number": ["12343960"] * 30,
        "Transaction Description": [
            "BLOOM LP WAGES", "Holiday Shopping", "Mortgage",
            "Black Friday", "Council Tax",
            "Stock Dividend", "Coffee Subscription", "Insurance",
            "Restaurant Week", "Health Insurance",
            "BLOOM LP WAGES", "Movie Theater", "NARISTER OLIVEIRA",
            "Utilities Bundle", "Taxi Service",
            "BLOOM LP WAGES", "Airline Tickets", "Freelance Payment",
            "Fashion Outlet", "Rent Payment",
            "BLOOM LP WAGES", "Home Supplies", "PAIGE & PETROOK LI",
            "Home Decor", "Student Loan",
            "Music Concert", "Dental Bill",
            "BLOOM LP WAGES", "Tech Gadgets", "Grocery Shopping",
        ],
        "Debit Amount": [
            "", 445.00, 1200.00, 325.80, 244.00, "", 12.99, 385.00,
            156.40, 385.00, "", 45.00, 3000.00, 195.00, 35.00,
            "", 680.00, "", 215.60, 950.00, "", 89.50, 2250.00,
            178.90, 420.00, 95.00, 145.00, "", 1250.00, 156.75
        ],
        "Credit Amount": [
            9016.21, "", "", "", "", 850.00, "", "", "", "",
            9016.21, "", "", "", "", 9016.21, "", 3800.00, "", "",
            9016.21, "", "", "", "", "", "", 8547.52, "", ""
        ],
        "Balance": [
            18555.00, 18110.00, 16910.00, 16584.20, 16340.20, 17190.20,
            17177.21, 16792.21, 16635.81, 16250.81, 25267.02, 25222.02,
            22222.02, 22027.02, 21992.02, 31008.23, 30328.23, 34128.23,
            33912.63, 32962.63, 41978.84, 41889.34, 39639.34, 39460.44,
            39040.44, 38945.44, 38800.44, 47347.96, 46097.96, 45941.21
        ]
    }
    if year not in datasets:
        raise ValueError("No dataset available for the requested year")
    return pd.DataFrame(datasets[year])


def create_pipeline_dirs_with_files(base_path: Path, years=None):
    """Create input, output, metadata directories and populate input with CSVs.

    Returns a tuple (input_dir, output_dir, output_file, metadata_dir)
    """
    if years is None:
        years = [2025, 2024, 2023]

    input_dir = base_path / "input"
    input_dir.mkdir()

    output_dir = base_path / "output"
    output_dir.mkdir()
    output_file = output_dir / "combined_output.csv"

    metadata_dir = base_path / "metadata"
    metadata_dir.mkdir()

    for y in years:
        file_path = input_dir / f"{y}_transactions.csv"
        df = build_transactions_for_year(y)
        df.to_csv(file_path, index=False)

    return input_dir, output_dir, output_file, metadata_dir


def run_append_and_save_pipeline(input_dir: Path, output_file: Path, metadata_dir: Path):
    """Run a simple pipeline: AppendFilesCommand -> SaveFileCommand and return DataFrame + metadata.

    Returns (result_df, collector)
    """
    collector = MetadataCollector(pipeline_name="append_save_test_pipeline")
    pipeline_context = {"metadata_dir": str(metadata_dir.resolve())}
    pipeline = DataPipeline(
        commands=[
            AppendFilesCommand(input_dir=str(input_dir), file_glob="*.csv"),
            SaveFileCommand(output_path=str(output_file)),
        ],
        collector=collector,
        context=pipeline_context,
    )
    result_df = pipeline.run(None)
    return result_df, collector


def assert_pipeline_output(result_df: pd.DataFrame, saved_df: pd.DataFrame, expected_row_count: int):
    assert result_df is not None, "Pipeline should return a DataFrame"
    assert not result_df.empty, "Result DataFrame should not be empty"
    assert len(result_df) == expected_row_count, f"Expected {expected_row_count} rows, got {len(result_df)}"
    assert len(saved_df) == expected_row_count, f"Saved file should have {expected_row_count} rows, got {len(saved_df)}"
    pd.testing.assert_frame_equal(
        result_df.reset_index(drop=True),
        saved_df.reset_index(drop=True),
        check_dtype=False,
        obj="Pipeline output should match saved file",
    )


def assert_pipeline_metadata(collector: MetadataCollector, metadata_dir: Path, expected_row_count: int):
    metadata = collector.get_pipeline_metadata()
    assert len(metadata.steps) == 2, f"Pipeline should have 2 steps, got {len(metadata.steps)}"
    assert metadata.steps[0].name == "AppendFilesCommand", "First step should be AppendFilesCommand"
    assert metadata.steps[1].name == "SaveFileCommand", "Second step should be SaveFileCommand"
    assert "input_dir" in metadata.steps[0].parameters, "AppendFilesCommand should capture input_dir parameter"
    assert "file_glob" in metadata.steps[0].parameters, "AppendFilesCommand should capture file_glob parameter"
    assert "output_file_path" in metadata.steps[1].parameters, "SaveFileCommand should capture output_file_path parameter"
    assert metadata.steps[0].input_rows == 0, "AppendFilesCommand should start with 0 input rows"
    assert metadata.steps[0].output_rows == expected_row_count, f"AppendFilesCommand should output {expected_row_count} rows"
    assert metadata.steps[1].input_rows == expected_row_count, f"SaveFileCommand should receive {expected_row_count} input rows"
    assert metadata.steps[1].output_rows == expected_row_count, f"SaveFileCommand should output {expected_row_count} rows"
    assert hasattr(metadata, "context_files"), "Pipeline metadata should include context_files"
    assert metadata.context_files is not None, "context_files should not be None"
    assert "metadata_dir" in metadata.context_files, "metadata_dir should be present in pipeline context_files"
    assert metadata.context_files["metadata_dir"] == str(metadata_dir.resolve()), "metadata_dir in metadata.context_files should match the created metadata directory"


def test_append_and_save_pipeline_configuration():
    """Test pipeline configuration with AppendFilesCommand and SaveFileCommand only."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        input_dir, output_dir, output_file, metadata_dir = create_pipeline_dirs_with_files(temp_path)
        
        result_df, collector = run_append_and_save_pipeline(input_dir, output_file, metadata_dir)
        
        assert result_df is not None, "Pipeline should return a DataFrame"
        assert not result_df.empty, "Result DataFrame should not be empty"
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        
        saved_df = pd.read_csv(output_file)
        expected_row_count = 90
        assert_pipeline_output(result_df, saved_df, expected_row_count)
        
        expected_columns = ["Transaction Date", "Transaction Type", "Sort Code",
                          "Account Number", "Transaction Description", 
                          "Debit Amount", "Credit Amount", "Balance"]
        assert list(saved_df.columns) == expected_columns, f"Columns should be {expected_columns}, got {list(saved_df.columns)}"
        
        assert saved_df["Transaction Date"].dtype == object, "Transaction Date should be string/object type"
        assert saved_df["Transaction Type"].dtype == object, "Transaction Type should be string/object type"
        assert saved_df["Transaction Description"].dtype == object, "Transaction Description should be string/object type"
        
        assert "2025" in saved_df.iloc[0]["Transaction Date"], "First transaction should be from 2025 (files sorted in reverse order)"
        
        assert "2024" in saved_df.iloc[30]["Transaction Date"], "Transaction at row 30 should be from 2024"
        assert "2023" in saved_df.iloc[-1]["Transaction Date"], "Last transaction should be from 2023"
        
        valid_types = {"DEB", "DD", "FPI", "BGC", "FPO", "SO", "CPT", "TFR"}
        assert set(saved_df["Transaction Type"].unique()).issubset(valid_types), f"All transaction types should be in {valid_types}"
        
        assert not saved_df["Transaction Date"].isnull().any(), "Transaction Date should not have null values"
        assert not saved_df["Transaction Type"].isnull().any(), "Transaction Type should not have null values"
        assert not saved_df["Balance"].isnull().any(), "Balance should not have null values"
        
        
        
        assert_pipeline_metadata(collector, metadata_dir, expected_row_count)

        print(f"\n✅ Test passed successfully!")
        print(f"   - Loaded and combined 3 files ({expected_row_count} transactions)")
        print(f"   - Input matches output (identity pipeline)")
        print(f"   - Pipeline metadata correctly captured")
        print(f"   - Metadata directory context preserved")
        print(f"   - All data integrity checks passed")

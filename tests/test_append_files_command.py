import pandas as pd
import pytest
from tempfile import TemporaryDirectory
from analyzer.pipeline.pipeline_commands import AppendFilesCommand
from pathlib import Path

def test_append_files_command_with_realistic_data():
    """Test AppendFilesCommand with temporary files containing realistic data."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 3 temporary files with realistic data
        file_1 = temp_path / "2025_bos_1.csv"
        file_2 = temp_path / "2024_bos_2.csv"
        file_3 = temp_path / "2023_bos_3.csv"

        # File 1: 2025, descending dates, no duplicates
        file_1_data = pd.DataFrame({
            "TransactionDate": ["2025-12-31", "2025-12-30", "2025-12-29"],
            "TransactionType": ["DEB", "DD", "FPI"],
            "TransactionDescription": ["Coffee Shop", "Internet Bill", "Salary"],
            "TransactionValue": [-5.50, -45.00, 2500.00]
        })
        file_1_data.to_csv(file_1, index=False)

        # File 2: 2024, descending dates, with duplicates
        file_2_data = pd.DataFrame({
            "TransactionDate": ["2024-11-15", "2024-11-15", "2024-11-14"],
            "TransactionType": ["DEB", "DEB", "DD"],
            "TransactionDescription": ["Grocery Store", "Grocery Store", "Phone Bill"],
            "TransactionValue": [-85.30, -20.00, -60.00]
        })
        file_2_data.to_csv(file_2, index=False)

        # File 3: 2023, descending dates, no duplicates
        file_3_data = pd.DataFrame({
            "TransactionDate": ["2023-10-10", "2023-10-09", "2023-10-08"],
            "TransactionType": ["FPI", "DEB", "DD"],
            "TransactionDescription": ["Bonus", "Restaurant", "Electricity Bill"],
            "TransactionValue": [1500.00, -50.00, -100.00]
        })
        file_3_data.to_csv(file_3, index=False)

        # Run AppendFilesCommand
        command = AppendFilesCommand(input_dir=temp_path)
        result = command.process()

        # Assert the data is loaded in descending date order across all files
        expected_dates = [
            "2025-12-31", "2025-12-30", "2025-12-29",
            "2024-11-15", "2024-11-15", "2024-11-14",
            "2023-10-10", "2023-10-09", "2023-10-08"
        ]
        assert result["TransactionDate"].tolist() == expected_dates, "Dates should be in descending order across all files."
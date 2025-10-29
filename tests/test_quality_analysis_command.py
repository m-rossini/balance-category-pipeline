"""TDD: Tests for QualityAnalysisCommand."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import QualityAnalysisCommand
from analyzer.pipeline.quality import DefaultQualityCalculator


def test_quality_analysis_command_returns_command_result():
    """Test that QualityAnalysisCommand returns CommandResult."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport'],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Confidence': [0.95, 0.92]
    })
    
    command = QualityAnalysisCommand(calculator=DefaultQualityCalculator())
    result = command.process(df)
    
    # Check CommandResult structure
    assert result.return_code == 0
    assert result.data is not None
    assert result.error is None
    assert result.data.equals(df)  # Data should be unchanged


def test_quality_analysis_command_updates_metadata():
    """Test that QualityAnalysisCommand populates metadata_updates."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport'],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Confidence': [0.95, 0.92]
    })
    
    command = QualityAnalysisCommand(calculator=DefaultQualityCalculator())
    result = command.process(df)
    
    assert result.metadata_updates is not None
    assert 'quality_index' in result.metadata_updates
    assert 'calculator_name' in result.metadata_updates
    
    # Check values
    quality_index = result.metadata_updates['quality_index']
    assert quality_index == pytest.approx(0.935, abs=0.001)  # (0.95 + 0.92) / 2
    assert result.metadata_updates['calculator_name'] == 'DefaultQualityCalculator'


def test_quality_analysis_command_with_missing_data():
    """Test QualityAnalysisCommand with missing category."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', None],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Confidence': [0.95, 0.92]
    })
    
    command = QualityAnalysisCommand(calculator=DefaultQualityCalculator())
    result = command.process(df)
    
    assert result.return_code == 0
    assert result.metadata_updates['quality_index'] == pytest.approx(0.475, abs=0.001)  # (0.95 + 0) / 2


def test_quality_analysis_command_with_custom_calculator():
    """Test QualityAnalysisCommand with custom calculator."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food'],
        'SubCategoryAnnotation': ['Coffee'],
        'Confidence': [0.80]
    })
    
    class TestCalculator(DefaultQualityCalculator):
        """Custom calculator that always returns 0.5."""
        def calculate(self, df):
            return 0.5
    
    calculator = TestCalculator()
    command = QualityAnalysisCommand(calculator=calculator)
    result = command.process(df)
    
    assert result.metadata_updates['quality_index'] == 0.5
    assert result.metadata_updates['calculator_name'] == 'TestCalculator'

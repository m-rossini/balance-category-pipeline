"""Tests for QualityAnalysisCommand that analyzes data quality."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import QualityAnalysisCommand
from analyzer.workflows.quality_metrics import QualityMetrics
from analyzer.workflows.quality_reporter import QualityReporter


class MockQualityReporter(QualityReporter):
    """Mock reporter to capture metrics."""
    
    def __init__(self):
        self.metrics = None
    
    def report(self, metrics: QualityMetrics) -> None:
        """Store metrics for test verification."""
        self.metrics = metrics


def test_quality_analysis_command_analyzes_category_column():
    """Test that command analyzes Category column completeness."""
    df = pd.DataFrame({
        'TransactionNumber': [1, 2, 3, 4, 5],
        'Category': ['Food', 'Transport', None, 'Utilities', ''],
        'SubCategory': ['Groceries', 'Bus', None, 'Electric', ''],
        'Confidence': [0.9, 0.85, 0.0, 0.95, 0.0],
    })
    
    reporter = MockQualityReporter()
    command = QualityAnalysisCommand(
        columns=['Category', 'SubCategory', 'Confidence'],
        reporter=reporter
    )
    
    result_df = command.process(df)
    
    # Should return original dataframe unchanged
    assert result_df.equals(df)
    
    # Should have reported metrics
    assert reporter.metrics is not None
    
    # Category completeness: 3 out of 5 = 60%
    assert reporter.metrics.category_completeness == 60.0


def test_quality_analysis_command_analyzes_subcategory_column():
    """Test that command analyzes SubCategory column completeness."""
    df = pd.DataFrame({
        'TransactionNumber': [1, 2, 3, 4, 5],
        'Category': ['Food', 'Transport', 'Food', 'Utilities', 'Food'],
        'SubCategory': ['Groceries', 'Bus', None, 'Electric', ''],
        'Confidence': [0.9, 0.85, 0.7, 0.95, 0.8],
    })
    
    reporter = MockQualityReporter()
    command = QualityAnalysisCommand(
        columns=['Category', 'SubCategory', 'Confidence'],
        reporter=reporter
    )
    
    result_df = command.process(df)
    
    # SubCategory completeness: 3 out of 5 = 60%
    assert reporter.metrics.subcategory_completeness == 60.0


def test_quality_analysis_command_analyzes_confidence_scores():
    """Test that command analyzes Confidence column."""
    df = pd.DataFrame({
        'TransactionNumber': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Category': ['Food'] * 10,
        'SubCategory': ['Groceries'] * 10,
        'Confidence': [0.95, 0.90, 0.85, 0.80, 0.75, 0.65, 0.55, 0.45, 0.35, 0.15],
    })
    
    reporter = MockQualityReporter()
    command = QualityAnalysisCommand(
        columns=['Category', 'SubCategory', 'Confidence'],
        reporter=reporter
    )
    
    result_df = command.process(df)
    
    # Mean confidence should be average of all confidence values
    expected_mean = sum(df['Confidence']) / len(df['Confidence'])
    assert abs(reporter.metrics.mean_confidence - expected_mean) < 0.01
    
    # High confidence (> 0.7): indices 0,1,2,3,4 = 5 out of 10 = 50%
    assert reporter.metrics.high_confidence_rate == 50.0
    
    # Medium confidence (0.4 < c <= 0.7): indices 5,6,7 = 3 out of 10 = 30%
    assert reporter.metrics.medium_confidence_rate == 30.0
    
    # Low confidence (<= 0.4): indices 8,9 = 2 out of 10 = 20%
    assert reporter.metrics.low_confidence_rate == 20.0


def test_quality_analysis_command_overall_quality_index():
    """Test that command generates overall quality index."""
    df = pd.DataFrame({
        'TransactionNumber': range(1, 101),
        'Category': ['Food'] * 100,
        'SubCategory': ['Groceries'] * 100,
        'Confidence': [0.85] * 100,
    })
    
    reporter = MockQualityReporter()
    command = QualityAnalysisCommand(
        columns=['Category', 'SubCategory', 'Confidence'],
        reporter=reporter
    )
    
    result_df = command.process(df)
    
    # Perfect data should have high quality index (>= 80)
    overall_index = reporter.metrics.calculate_overall_quality_index()
    assert overall_index >= 80.0


def test_quality_analysis_command_with_optional_reporter():
    """Test that command works without reporter (optional dependency injection)."""
    df = pd.DataFrame({
        'TransactionNumber': [1, 2, 3],
        'Category': ['Food', 'Transport', 'Utilities'],
        'SubCategory': ['Groceries', 'Bus', 'Electric'],
        'Confidence': [0.9, 0.85, 0.95],
    })
    
    # Should work without reporter
    command = QualityAnalysisCommand(
        columns=['Category', 'SubCategory', 'Confidence'],
        reporter=None
    )
    
    result_df = command.process(df)
    
    # Should return original dataframe
    assert result_df.equals(df)


def test_quality_analysis_command_returns_dataframe_unchanged():
    """Test that command returns the dataframe unchanged."""
    df = pd.DataFrame({
        'TransactionNumber': [1, 2, 3],
        'Category': ['Food', 'Transport', 'Utilities'],
        'SubCategory': ['Groceries', 'Bus', 'Electric'],
        'Confidence': [0.9, 0.85, 0.95],
    })
    
    reporter = MockQualityReporter()
    command = QualityAnalysisCommand(
        columns=['Category', 'SubCategory', 'Confidence'],
        reporter=reporter
    )
    
    result_df = command.process(df)
    
    # DataFrame should be returned unchanged (pass-through command)
    assert result_df.equals(df)
    assert len(result_df) == 3

"""Tests for quality reporter interface and implementations."""
import pytest
from analyzer.workflows.quality_metrics import QualityMetrics
from analyzer.workflows.quality_reporter import QualityReporter


class MockQualityReporter(QualityReporter):
    """Mock reporter for testing."""
    
    def __init__(self):
        self.reported_metrics = None
    
    def report(self, metrics: QualityMetrics) -> None:
        """Store metrics for verification."""
        self.reported_metrics = metrics


def test_quality_reporter_can_be_implemented():
    """Test that QualityReporter can be subclassed."""
    reporter = MockQualityReporter()
    assert reporter is not None
    assert isinstance(reporter, QualityReporter)


def test_quality_reporter_report_method_receives_metrics():
    """Test that report method receives QualityMetrics correctly."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=80.0,
        confidence_completeness=90.0,
        mean_confidence=0.75,
        min_confidence=0.0,
        max_confidence=1.0,
        high_confidence_rate=70.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=10.0,
        subcategory_consistency=100.0,
        total_rows=1000,
    )
    
    reporter = MockQualityReporter()
    reporter.report(metrics)
    
    assert reporter.reported_metrics is not None
    assert reporter.reported_metrics.total_rows == 1000
    assert reporter.reported_metrics.category_completeness == 100.0


def test_multiple_reporters_can_be_created():
    """Test that multiple independent reporter instances work."""
    reporter1 = MockQualityReporter()
    reporter2 = MockQualityReporter()
    
    metrics1 = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=80.0,
        confidence_completeness=90.0,
        mean_confidence=0.75,
        min_confidence=0.0,
        max_confidence=1.0,
        high_confidence_rate=70.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=10.0,
        subcategory_consistency=100.0,
        total_rows=1000,
    )
    
    metrics2 = QualityMetrics(
        category_completeness=95.0,
        subcategory_completeness=75.0,
        confidence_completeness=85.0,
        mean_confidence=0.70,
        min_confidence=0.1,
        max_confidence=0.99,
        high_confidence_rate=60.0,
        medium_confidence_rate=25.0,
        low_confidence_rate=15.0,
        subcategory_consistency=95.0,
        total_rows=500,
    )
    
    reporter1.report(metrics1)
    reporter2.report(metrics2)
    
    assert reporter1.reported_metrics.total_rows == 1000
    assert reporter2.reported_metrics.total_rows == 500

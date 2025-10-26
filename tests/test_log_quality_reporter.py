"""Tests for LogQualityReporter that logs quality metrics."""
import pytest
import logging
from analyzer.workflows.quality_metrics import QualityMetrics
from analyzer.workflows.log_quality_reporter import LogQualityReporter


def test_log_quality_reporter_can_be_instantiated():
    """Test that LogQualityReporter can be created."""
    reporter = LogQualityReporter()
    assert reporter is not None


def test_log_quality_reporter_logs_metrics(caplog):
    """Test that LogQualityReporter logs metrics with overall quality index."""
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
    
    reporter = LogQualityReporter()
    
    with caplog.at_level(logging.INFO):
        reporter.report(metrics)
    
    # Should log something about quality
    assert len(caplog.records) > 0
    assert 'quality' in caplog.text.lower() or 'index' in caplog.text.lower()


def test_log_quality_reporter_logs_completeness(caplog):
    """Test that LogQualityReporter logs completeness metrics."""
    metrics = QualityMetrics(
        category_completeness=95.5,
        subcategory_completeness=87.3,
        confidence_completeness=92.1,
        mean_confidence=0.75,
        min_confidence=0.0,
        max_confidence=1.0,
        high_confidence_rate=70.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=10.0,
        subcategory_consistency=100.0,
        total_rows=1000,
    )
    
    reporter = LogQualityReporter()
    
    with caplog.at_level(logging.INFO):
        reporter.report(metrics)
    
    # Should mention completeness in logs
    log_text = caplog.text.lower()
    assert 'completeness' in log_text or 'category' in log_text


def test_log_quality_reporter_logs_confidence(caplog):
    """Test that LogQualityReporter logs confidence metrics."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=100.0,
        confidence_completeness=100.0,
        mean_confidence=0.78,
        min_confidence=0.1,
        max_confidence=0.99,
        high_confidence_rate=75.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=5.0,
        subcategory_consistency=100.0,
        total_rows=2000,
    )
    
    reporter = LogQualityReporter()
    
    with caplog.at_level(logging.INFO):
        reporter.report(metrics)
    
    # Should mention confidence in logs
    log_text = caplog.text.lower()
    assert 'confidence' in log_text or 'mean' in log_text


def test_log_quality_reporter_logs_consistency(caplog):
    """Test that LogQualityReporter logs consistency metrics."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=100.0,
        confidence_completeness=100.0,
        mean_confidence=0.85,
        min_confidence=0.5,
        max_confidence=1.0,
        high_confidence_rate=80.0,
        medium_confidence_rate=15.0,
        low_confidence_rate=5.0,
        subcategory_consistency=98.5,
        total_rows=1500,
    )
    
    reporter = LogQualityReporter()
    
    with caplog.at_level(logging.INFO):
        reporter.report(metrics)
    
    # Should mention consistency or subcategory in logs
    log_text = caplog.text.lower()
    assert 'consistency' in log_text or 'subcategory' in log_text


def test_log_quality_reporter_logs_total_rows(caplog):
    """Test that LogQualityReporter logs total rows analyzed."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=100.0,
        confidence_completeness=100.0,
        mean_confidence=0.80,
        min_confidence=0.5,
        max_confidence=1.0,
        high_confidence_rate=75.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=5.0,
        subcategory_consistency=100.0,
        total_rows=5432,
    )
    
    reporter = LogQualityReporter()
    
    with caplog.at_level(logging.INFO):
        reporter.report(metrics)
    
    # Should mention rows in logs
    log_text = caplog.text.lower()
    assert 'rows' in log_text or '5432' in log_text


def test_log_quality_reporter_is_quality_reporter():
    """Test that LogQualityReporter is a QualityReporter."""
    from analyzer.workflows.quality_reporter import QualityReporter
    reporter = LogQualityReporter()
    assert isinstance(reporter, QualityReporter)

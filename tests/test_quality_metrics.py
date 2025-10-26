"""Tests for quality metrics data structure and calculations."""
import pytest
from analyzer.workflows.quality_metrics import QualityMetrics


def test_quality_metrics_completeness_score():
    """Test that completeness score is average of three metrics."""
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
    
    # (100 + 80 + 90) / 3 = 90.0
    assert metrics.calculate_completeness_score() == 90.0


def test_quality_metrics_confidence_score():
    """Test confidence score calculation with weighted high/medium rates."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=100.0,
        confidence_completeness=100.0,
        mean_confidence=0.75,
        min_confidence=0.0,
        max_confidence=1.0,
        high_confidence_rate=70.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=10.0,
        subcategory_consistency=100.0,
        total_rows=1000,
    )
    
    # (70 * 1.0 + 20 * 0.5) / 1.5 = (70 + 10) / 1.5 ≈ 53.33
    assert abs(metrics.calculate_confidence_score() - 53.33) < 0.01


def test_quality_metrics_overall_quality_index():
    """Test weighted overall quality index calculation (20% + 60% + 20%)."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=95.0,
        confidence_completeness=90.0,
        mean_confidence=0.75,
        min_confidence=0.0,
        max_confidence=1.0,
        high_confidence_rate=80.0,
        medium_confidence_rate=15.0,
        low_confidence_rate=5.0,
        subcategory_consistency=100.0,
        total_rows=1000,
    )
    
    overall = metrics.calculate_overall_quality_index()
    assert 73.0 < overall < 75.0


def test_quality_metrics_to_dict():
    """Test conversion to dictionary for serialization."""
    metrics = QualityMetrics(
        category_completeness=100.0,
        subcategory_completeness=80.0,
        confidence_completeness=90.0,
        mean_confidence=0.75,
        min_confidence=0.1,
        max_confidence=0.99,
        high_confidence_rate=70.0,
        medium_confidence_rate=20.0,
        low_confidence_rate=10.0,
        subcategory_consistency=100.0,
        total_rows=1000,
    )
    
    result = metrics.to_dict()
    
    assert 'completeness' in result
    assert 'confidence' in result
    assert 'consistency' in result
    assert 'overall_quality_index' in result
    assert 'total_rows' in result
    assert result['total_rows'] == 1000

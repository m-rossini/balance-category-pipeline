"""TDD: Tests for QualityMetrics dataclass and quality calculations."""
import pytest
from analyzer.pipeline.quality import QualityMetrics


def test_quality_metrics_creation_with_all_fields():
    """Test that QualityMetrics can be created with all required fields."""
    metrics = QualityMetrics(
        completeness=0.95,
        confidence=0.87,
        consistency=0.92,
        overall_quality_index=0.91
    )
    
    assert metrics.completeness == 0.95
    assert metrics.confidence == 0.87
    assert metrics.consistency == 0.92
    assert metrics.overall_quality_index == 0.91


def test_quality_metrics_to_dict():
    """Test that QualityMetrics can be serialized to dict."""
    metrics = QualityMetrics(
        completeness=0.95,
        confidence=0.87,
        consistency=0.92,
        overall_quality_index=0.91
    )
    
    result_dict = metrics.to_dict()
    
    assert isinstance(result_dict, dict)
    assert result_dict['completeness'] == 0.95
    assert result_dict['confidence'] == 0.87
    assert result_dict['consistency'] == 0.92
    assert result_dict['overall_quality_index'] == 0.91

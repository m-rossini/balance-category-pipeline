"""TDD: Tests for QualityCalculator interface and implementations."""
import pytest
import pandas as pd
from analyzer.pipeline.quality import QualityCalculator, SimpleQualityCalculator, QualityMetrics


def test_default_quality_calculator_with_all_valid_data():
    """Test quality calculation with all valid, high-confidence data."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric'],
        'Confidence': [0.95, 0.92, 0.88]
    })
    
    calculator = SimpleQualityCalculator()
    metrics = calculator.calculate(df)
    
    # Average of [0.95, 0.92, 0.88] = 0.9167
    assert isinstance(metrics, QualityMetrics)
    assert metrics.overall_quality_index == pytest.approx(0.9167, abs=0.001)


def test_default_quality_calculator_with_zero_confidence():
    """Test that zero confidence makes entire row zero."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric'],
        'Confidence': [0.95, 0.0, 0.88]
    })
    
    calculator = SimpleQualityCalculator()
    metrics = calculator.calculate(df)
    
    # Row 2 has 0 confidence, so it's 0. Average of [0.95, 0, 0.88] = 0.6100
    assert isinstance(metrics, QualityMetrics)
    assert metrics.overall_quality_index == pytest.approx(0.6100, abs=0.001)


def test_default_quality_calculator_with_missing_category():
    """Test that missing category makes row zero."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', None, 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric'],
        'Confidence': [0.95, 0.92, 0.88]
    })
    
    calculator = SimpleQualityCalculator()
    metrics = calculator.calculate(df)
    
    # Row 2 has missing category, so it's 0. Average of [0.95, 0, 0.88] = 0.6100
    assert isinstance(metrics, QualityMetrics)
    assert metrics.overall_quality_index == pytest.approx(0.6100, abs=0.001)


def test_default_quality_calculator_with_missing_subcategory():
    """Test that missing subcategory makes row zero."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', None, 'Electric'],
        'Confidence': [0.95, 0.92, 0.88]
    })
    
    calculator = SimpleQualityCalculator()
    metrics = calculator.calculate(df)
    
    # Row 2 has missing subcategory, so it's 0. Average of [0.95, 0, 0.88] = 0.6100
    assert isinstance(metrics, QualityMetrics)
    assert metrics.overall_quality_index == pytest.approx(0.6100, abs=0.001)


def test_default_quality_calculator_with_low_confidence():
    """Test calculation with low confidence scores."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
        'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric'],
        'Confidence': [0.60, 0.92, 0.88]
    })
    
    calculator = SimpleQualityCalculator()
    metrics = calculator.calculate(df)
    
    # Currently using simple average: (0.60 + 0.92 + 0.88) / 3 = 0.8
    # Note: Weighting logic (low scores having more impact) to be clarified in future
    expected = (0.60 + 0.92 + 0.88) / 3
    assert isinstance(metrics, QualityMetrics)
    assert metrics.overall_quality_index == pytest.approx(expected, abs=0.001)


def test_default_quality_calculator_with_empty_dataframe():
    """Test calculation with empty DataFrame."""
    df = pd.DataFrame({
        'CategoryAnnotation': [],
        'SubCategoryAnnotation': [],
        'Confidence': []
    })
    
    calculator = SimpleQualityCalculator()
    metrics = calculator.calculate(df)
    
    # Empty data should result in 0 quality
    assert isinstance(metrics, QualityMetrics)
    assert metrics.overall_quality_index == 0.0

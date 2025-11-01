"""TDD: Tests for CompletenessCalculator - Phase 1."""
import pytest
import pandas as pd
from analyzer.pipeline.quality_completeness import CompletenessCalculator


def test_completeness_all_fields_present():
    """Test: CompletenessCalculator computes 1.0 when all fields present and non-empty."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport'],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Description': ['Breakfast', 'Morning commute']
    })
    
    calculator = CompletenessCalculator()
    completeness = calculator.calculate(df)
    
    # All 3 fields present and populated for both rows = 1.0
    assert completeness == pytest.approx(1.0)

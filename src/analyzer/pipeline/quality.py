"""Quality metrics calculation and tracking."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import pandas as pd

@dataclass
class QualityMetrics:
    """Represents quality metrics for a pipeline execution."""
    completeness: float
    confidence: float
    consistency: float
    overall_quality_index: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert quality metrics to dictionary for serialization."""
        return {
            "completeness": self.completeness,
            "confidence": self.confidence,
            "consistency": self.consistency,
            "overall_quality_index": self.overall_quality_index
        }


class QualityCalculator(ABC):
    """Abstract interface for pluggable quality calculation strategies."""

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> QualityMetrics:
        """Calculate quality metrics for DataFrame.
        
        Args:
            df: DataFrame with CategoryAnnotation, SubCategoryAnnotation, Confidence columns
            
        Returns:
            QualityMetrics object with calculated metrics
        """
        pass


class SimpleQualityCalculator(QualityCalculator):
    """Simple implementation of quality calculator with confidence-based calculation.
    
    Rules:
    - Row is invalid (0) if any of: category, subcategory, or confidence is missing
    - Row is invalid (0) if confidence is 0
    - Confidence values < 0.70 have more weight in bringing index down
    - Confidence values 0.71-0.90 have second weight
    - Confidence values > 0.90 have lesser weight
    """

    def calculate(self, df: pd.DataFrame) -> QualityMetrics:
        """Calculate weighted quality index based on row confidence scores."""
        if df.empty:
            return QualityMetrics(
                completeness=0.0,
                confidence=0.0,
                consistency=0.0,
                overall_quality_index=0.0
            )

        # Calculate row-level scores
        row_scores = []
        for idx, row in df.iterrows():
            row_score = self._calculate_row_score(row)
            row_scores.append(row_score)

        if not row_scores:
            return QualityMetrics(
                completeness=0.0,
                confidence=0.0,
                consistency=0.0,
                overall_quality_index=0.0
            )

        # Apply weighted average calculation
        quality_index = self._apply_weighting(row_scores)
        
        return QualityMetrics(
            completeness=0.0,  # To be calculated in future
            confidence=quality_index,
            consistency=0.0,  # To be calculated in future
            overall_quality_index=quality_index
        )

    def _calculate_row_score(self, row: pd.Series) -> float:
        """Calculate score for a single row. Returns 0 if any field missing or confidence is 0."""
        # Check for missing values
        if (pd.isna(row.get('CategoryAnnotation')) or
            pd.isna(row.get('SubCategoryAnnotation')) or
            pd.isna(row.get('Confidence'))):
            return 0.0

        # Check if category or subcategory are empty strings (whitespace)
        category = str(row.get('CategoryAnnotation', '')).strip()
        subcategory = str(row.get('SubCategoryAnnotation', '')).strip()
        
        if not category or not subcategory:
            return 0.0

        # Get confidence value
        confidence = float(row.get('Confidence', 0))
        
        # If confidence is 0, row is invalid
        if confidence == 0.0:
            return 0.0

        return confidence

    def _apply_weighting(self, scores: list) -> float:
        """Apply weighted calculation where low scores have more impact.
        
        Currently using simple average. Weighting logic to be clarified:
        - Low scores (< 0.70): Higher impact
        - Mid scores (0.71-0.90): Medium impact  
        - High scores (> 0.90): Lower impact
        """
        if not scores:
            return 0.0

        # For now, use simple average
        return sum(scores) / len(scores)


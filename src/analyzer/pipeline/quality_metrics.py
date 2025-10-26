"""Data structures and utilities for data quality analysis."""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class QualityMetrics:
    """Holds quality analysis results for a dataset."""
    
    # Completeness metrics (20% weight)
    category_completeness: float  # % of non-empty Category values (0-100)
    subcategory_completeness: float  # % of non-empty SubCategory values (0-100)
    confidence_completeness: float  # % of non-null Confidence values (0-100)
    
    # Confidence metrics (60% weight)
    mean_confidence: float  # Average confidence score
    min_confidence: float  # Minimum confidence score
    max_confidence: float  # Maximum confidence score
    high_confidence_rate: float  # % of rows with confidence > 0.7 (0-100)
    medium_confidence_rate: float  # % of rows 0.4 < confidence <= 0.7 (0-100)
    low_confidence_rate: float  # % of rows with confidence <= 0.4 (0-100)
    
    # Consistency metrics (20% weight)
    subcategory_consistency: float  # % of subcategories only present with categories (0-100)
    total_rows: int  # Total rows analyzed
    
    def calculate_completeness_score(self) -> float:
        """Calculate average completeness score (0-100)."""
        return (self.category_completeness + self.subcategory_completeness + self.confidence_completeness) / 3
    
    def calculate_confidence_score(self) -> float:
        """Calculate average confidence score (0-100)."""
        # High confidence weighted higher than medium which is weighted higher than low
        return (self.high_confidence_rate * 1.0 + self.medium_confidence_rate * 0.5) / 1.5
    
    def calculate_consistency_score(self) -> float:
        """Calculate consistency score (0-100)."""
        return self.subcategory_consistency
    
    def calculate_overall_quality_index(self) -> float:
        """Calculate weighted overall quality index (0-100).
        
        Weights:
        - Completeness: 20%
        - Confidence: 60%
        - Consistency: 20%
        """
        completeness = self.calculate_completeness_score()
        confidence = self.calculate_confidence_score()
        consistency = self.calculate_consistency_score()
        
        overall = (
            completeness * 0.20 +
            confidence * 0.60 +
            consistency * 0.20
        )
        
        return round(overall, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'completeness': {
                'category': round(self.category_completeness, 2),
                'subcategory': round(self.subcategory_completeness, 2),
                'confidence': round(self.confidence_completeness, 2),
                'average': round(self.calculate_completeness_score(), 2),
            },
            'confidence': {
                'mean': round(self.mean_confidence, 4),
                'min': round(self.min_confidence, 4),
                'max': round(self.max_confidence, 4),
                'high_rate': round(self.high_confidence_rate, 2),
                'medium_rate': round(self.medium_confidence_rate, 2),
                'low_rate': round(self.low_confidence_rate, 2),
                'score': round(self.calculate_confidence_score(), 2),
            },
            'consistency': {
                'subcategory_dependency': round(self.subcategory_consistency, 2),
            },
            'overall_quality_index': self.calculate_overall_quality_index(),
            'total_rows': self.total_rows,
        }

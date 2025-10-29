"""Quality metrics calculation and tracking."""
from dataclasses import dataclass
from typing import Any, Dict, Optional


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

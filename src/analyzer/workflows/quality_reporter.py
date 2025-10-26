"""Abstract interface for quality metrics reporting."""
from abc import ABC, abstractmethod
from .quality_metrics import QualityMetrics


class QualityReporter(ABC):
    """Abstract base class for reporting quality analysis results.
    
    Allows flexible implementations: logging, metadata storage, CSV files, etc.
    """
    
    @abstractmethod
    def report(self, metrics: QualityMetrics) -> None:
        """Report quality metrics using the specific implementation.
        
        Args:
            metrics: QualityMetrics instance containing analysis results
        """
        pass

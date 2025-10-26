"""Quality reporter implementation that logs metrics."""
import logging
from .quality_metrics import QualityMetrics
from .quality_reporter import QualityReporter


class LogQualityReporter(QualityReporter):
    """Reports quality metrics by logging them."""
    
    def __init__(self, logger: logging.Logger = None):
        """Initialize log quality reporter.
        
        Args:
            logger: Optional logger instance (uses root logger if not provided)
        """
        self.logger = logger or logging.getLogger()
    
    def report(self, metrics: QualityMetrics) -> None:
        """Report quality metrics by logging detailed analysis.
        
        Args:
            metrics: QualityMetrics instance containing analysis results
        """
        overall_index = metrics.calculate_overall_quality_index()
        
        # Log overall quality index
        self.logger.info(f"[QualityAnalysis] Overall Quality Index: {overall_index:.2f}/100")
        
        # Log completeness metrics
        completeness_score = metrics.calculate_completeness_score()
        self.logger.info(f"[QualityAnalysis] Completeness (20% weight): {completeness_score:.2f}% - Category: {metrics.category_completeness:.2f}%, SubCategory: {metrics.subcategory_completeness:.2f}%, Confidence: {metrics.confidence_completeness:.2f}%")
        
        # Log confidence metrics
        confidence_score = metrics.calculate_confidence_score()
        self.logger.info(f"[QualityAnalysis] Confidence (60% weight): {confidence_score:.2f}% - Mean: {metrics.mean_confidence:.4f}, High: {metrics.high_confidence_rate:.2f}%, Medium: {metrics.medium_confidence_rate:.2f}%, Low: {metrics.low_confidence_rate:.2f}%")
        
        # Log consistency metrics
        consistency_score = metrics.calculate_consistency_score()
        self.logger.info(f"[QualityAnalysis] Consistency (20% weight): {consistency_score:.2f}% - SubCategory Dependency: {metrics.subcategory_consistency:.2f}%")
        
        # Log total rows analyzed
        self.logger.info(f"[QualityAnalysis] Analyzed {metrics.total_rows} rows")

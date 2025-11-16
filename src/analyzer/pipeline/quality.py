"""Quality metrics calculation and tracking."""
import pandas as pd
import logging

from abc import ABC, abstractmethod
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
            "overall_quality_index": self.overall_quality_index,
        }


class QualityDimensionCalculator(ABC):
    """Abstract interface for individual quality dimension calculators."""
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> float:
        """Calculate quality score for this dimension.

        Args:
            df: DataFrame with categorization results

        Returns:
            Float between 0.0 and 1.0 representing quality for this dimension
        """
        pass


class CompletenessCalculator(QualityDimensionCalculator):
    """Calculates completeness quality dimension based on field presence."""
    def calculate(self, df: pd.DataFrame) -> float:
        """Calculate completeness score for the dataframe."""
        if df.empty:
            return 0.0

        # Calculate row-level completeness scores
        row_scores = []
        for idx, row in df.iterrows():
            row_score = self._calculate_row_completeness(row)
            row_scores.append(row_score)

        if not row_scores:
            return 0.0

        # Apply weighted average calculation
        completeness_score = self._apply_completeness_weighting(row_scores)
        return completeness_score

    def _calculate_row_completeness(self, row: pd.Series) -> float:
        """Calculate completeness score for a single row."""
        required_fields = ["CategoryAnnotation", "SubCategoryAnnotation", "Confidence"]
        present_fields = 0

        for field in required_fields:
            value = row.get(field)
            if not pd.isna(value) and str(value).strip():
                present_fields += 1

        return present_fields / len(required_fields)

    def _apply_completeness_weighting(self, scores: list) -> float:
        """Apply weighting to completeness scores."""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)


class ConfidenceCalculator(QualityDimensionCalculator):
    """Calculates confidence dimension of quality assessment.

    Confidence measures the reliability of categorization based on AI confidence scores.
    Applies weighted calculation where low confidence scores have more impact.

    Rules:
    - Row is invalid (0) if confidence is missing or 0
    - Confidence values < 0.70 have highest weight in bringing index down
    - Confidence values 0.71-0.90 have medium weight
    - Confidence values > 0.90 have lowest weight (highest quality)
    """
    def calculate(self, df: pd.DataFrame) -> float:
        """Calculate confidence score for DataFrame.

        Args:
            df: DataFrame with Confidence column

        Returns:
            Float between 0.0 (no valid confidence) and 1.0 (all high confidence)
        """
        if df.empty:
            return 0.0

        valid_scores = []
        for _, row in df.iterrows():
            score = self._calculate_row_confidence(row)
            if score > 0:  # Only include valid (non-zero) scores
                valid_scores.append(score)

        if not valid_scores:
            return 0.0

        # Apply weighted calculation
        return self._apply_confidence_weighting(valid_scores)

    def _calculate_row_confidence(self, row: pd.Series) -> float:
        """Calculate confidence score for a single row.

        Returns:
            Confidence value if valid, 0.0 if invalid/missing
        """
        confidence = row.get("Confidence")

        # Check for missing or invalid confidence
        if pd.isna(confidence):
            return 0.0

        try:
            conf_value = float(confidence)
            # If confidence is 0, row is invalid
            if conf_value == 0.0:
                return 0.0
            # Ensure confidence is in valid range
            return max(0.0, min(1.0, conf_value))
        except (ValueError, TypeError):
            return 0.0

    def _apply_confidence_weighting(self, scores: list) -> float:
        """Apply weighted calculation where low scores have more impact.

        Weighting logic:
        - Scores < 0.70: Weight = 3 (highest impact)
        - Scores 0.71-0.90: Weight = 2 (medium impact)
        - Scores > 0.90: Weight = 1 (lowest impact)

        Returns weighted average where low confidence has more impact.
        """
        if not scores:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for score in scores:
            if score < 0.70:
                weight = 3.0
            elif score <= 0.90:
                weight = 2.0
            else:
                weight = 1.0

            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0


class ConsistencyCalculator(QualityDimensionCalculator):
    """Calculates consistency dimension of quality assessment.

    Consistency measures how consistent categorizations are within similar transaction patterns.
    Analyzes whether similar transaction descriptions receive consistent categorizations.

    Rules:
    - Group transactions by similar descriptions (first 10-15 characters)
    - Calculate consistency as fraction of groups with uniform categorization
    - Penalize groups with mixed categorizations
    """
    def calculate(self, df: pd.DataFrame) -> float:
        """Calculate consistency score for DataFrame.

        Args:
            df: DataFrame with TransactionDescription, CategoryAnnotation, SubCategoryAnnotation

        Returns:
            Float between 0.0 (no consistency) and 1.0 (perfect consistency)
        """
        if df.empty:
            return 0.0

        # Group by description prefix and analyze consistency
        description_groups = self._group_by_description_prefix(df)

        if not description_groups:
            return 0.0

        consistent_groups = 0
        total_groups = len(description_groups)

        for group_df in description_groups.values():
            if self._is_group_consistent(group_df):
                consistent_groups += 1

        return consistent_groups / total_groups if total_groups > 0 else 0.0

    def _group_by_description_prefix(self, df: pd.DataFrame, prefix_length: int = 12) -> Dict[str, pd.DataFrame]:
        """Group transactions by description prefix.

        Args:
            df: DataFrame with TransactionDescription column
            prefix_length: Length of prefix to group by

        Returns:
            Dict mapping prefix to DataFrame group
        """
        groups = {}

        for _, row in df.iterrows():
            desc = str(row.get("TransactionDescription", "")).strip()
            if not desc:
                continue

            prefix = desc[:prefix_length].upper()

            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append(row)

        # Convert lists to DataFrames
        return {prefix: pd.DataFrame(rows) for prefix, rows in groups.items() if len(rows) > 1}

    def _is_group_consistent(self, group_df: pd.DataFrame) -> bool:
        """Check if a group has consistent categorizations.

        Args:
            group_df: DataFrame group with same description prefix

        Returns:
            True if all categorizations are identical, False otherwise
        """
        if group_df.empty or len(group_df) < 2:
            return True  # Single transactions are trivially consistent

        # Get unique categorizations
        categories = set()
        subcategories = set()

        for _, row in group_df.iterrows():
            cat = str(row.get("CategoryAnnotation", "")).strip()
            subcat = str(row.get("SubCategoryAnnotation", "")).strip()

            if cat and subcat:
                categories.add(cat)
                subcategories.add((cat, subcat))

        # Group is consistent if there's only one unique category+subcategory combination
        return len(subcategories) == 1


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


class DefaultQualityCalculator(QualityCalculator):
    """Default quality calculator that combines all three quality dimensions.

    Uses configurable dimension calculators to compute completeness, confidence,
    and consistency scores, then combines them into an overall quality index.
    """
    def __init__(
        self,
        completeness_calculator: Optional[QualityDimensionCalculator] = None,
        confidence_calculator: Optional[QualityDimensionCalculator] = None,
        consistency_calculator: Optional[QualityDimensionCalculator] = None,
        completeness_weight: float = 0.3,
        confidence_weight: float = 0.5,
        consistency_weight: float = 0.2,
    ):
        """Initialize with dimension calculators and weights.

        Args:
            completeness_calculator: Calculator for completeness dimension
            confidence_calculator: Calculator for confidence dimension
            consistency_calculator: Calculator for consistency dimension
            completeness_weight: Weight for completeness in overall index (default 0.3)
            confidence_weight: Weight for confidence in overall index (default 0.5)
            consistency_weight: Weight for consistency in overall index (default 0.2)
        """
        self.completeness_calculator = completeness_calculator or CompletenessCalculator()
        self.confidence_calculator = confidence_calculator or ConfidenceCalculator()
        self.consistency_calculator = consistency_calculator or ConsistencyCalculator()

        # Validate weights sum to 1.0
        total_weight = completeness_weight + confidence_weight + consistency_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Quality dimension weights must sum to 1.0, got {total_weight}")

        self.completeness_weight = completeness_weight
        self.confidence_weight = confidence_weight
        self.consistency_weight = consistency_weight

    def calculate(self, df: pd.DataFrame) -> QualityMetrics:
        """Calculate all quality dimensions and overall index."""
        if df.empty:
            return QualityMetrics(
                completeness=0.0,
                confidence=0.0,
                consistency=0.0,
                overall_quality_index=0.0,
            )

        # Calculate each dimension
        completeness = self.completeness_calculator.calculate(df)
        confidence = self.confidence_calculator.calculate(df)
        consistency = self.consistency_calculator.calculate(df)

        # Calculate overall quality index as weighted average
        overall_quality_index = (completeness * self.completeness_weight + confidence * self.confidence_weight +
                                 consistency * self.consistency_weight)

        return QualityMetrics(
            completeness=completeness,
            confidence=confidence,
            consistency=consistency,
            overall_quality_index=overall_quality_index,
        )


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
        """Calculate simple quality index based only on confidence scores."""
        if df.empty:
            logging.debug("[SimpleQualityCalculator] Empty DataFrame, returning zero metrics")
            return QualityMetrics(
                completeness=0.0,
                confidence=0.0,
                consistency=0.0,
                overall_quality_index=0.0,
            )

        logging.info(f"[SimpleQualityCalculator] Processing {len(df)} rows with iterrows()...")
        
        # Calculate row-level scores
        row_scores = []
        row_count = 0
        for idx, row in df.iterrows():
            row_score = self._calculate_row_confidence_score(row)
            row_scores.append(row_score)
            row_count += 1
            
        if not row_scores:
            logging.warning("[SimpleQualityCalculator] No valid row scores found")
            return QualityMetrics(
                completeness=0.0,
                confidence=0.0,
                consistency=0.0,
                overall_quality_index=0.0,
            )

        # Apply weighted average calculation
        quality_index = self._apply_confidence_weighting(row_scores)
        
        logging.info(f"[SimpleQualityCalculator] Completed with quality_index={quality_index:.4f}")

        return QualityMetrics(
            completeness=0.0,  # Not calculated in simple version
            confidence=quality_index,
            consistency=0.0,  # Not calculated in simple version
            overall_quality_index=quality_index,
        )

    def _calculate_row_confidence_score(self, row: pd.Series) -> float:
        """Calculate score for a single row. Returns 0 if any field missing or confidence is 0."""
        # Check for missing values
        if (pd.isna(row.get("CategoryAnnotation")) or pd.isna(row.get("SubCategoryAnnotation")) or pd.isna(row.get("Confidence"))):
            return 0.0

        # Check if category or subcategory are empty strings (whitespace)
        category = str(row.get("CategoryAnnotation", "")).strip()
        subcategory = str(row.get("SubCategoryAnnotation", "")).strip()

        if not category or not subcategory:
            return 0.0

        # Get confidence value
        confidence = float(row.get("Confidence", 0))

        # If confidence is 0, row is invalid
        if confidence == 0.0:
            return 0.0

        return confidence

    def _apply_confidence_weighting(self, scores: list) -> float:
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

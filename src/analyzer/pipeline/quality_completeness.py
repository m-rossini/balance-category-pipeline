"""Completeness dimension calculator for quality metrics."""
import pandas as pd


class CompletenessCalculator:
    """Calculates completeness dimension of quality assessment.
    
    Completeness measures the fraction of required fields that are present
    and populated (non-empty) across the dataset.
    
    Required fields:
    - CategoryAnnotation
    - SubCategoryAnnotation
    - Description
    """
    
    REQUIRED_FIELDS = ['CategoryAnnotation', 'SubCategoryAnnotation', 'Description']
    
    def calculate(self, df: pd.DataFrame) -> float:
        """Calculate completeness score for DataFrame.
        
        Completeness = Average fraction of required fields present across all rows
        
        Args:
            df: DataFrame containing the required fields
            
        Returns:
            Float between 0.0 (all fields missing) and 1.0 (all fields present)
            Empty DataFrames return 0.0
        """
        if df.empty:
            return 0.0
        
        row_scores = []
        for _, row in df.iterrows():
            score = self._calculate_row_completeness(row)
            row_scores.append(score)
        
        # Return average completeness across all rows
        return sum(row_scores) / len(row_scores) if row_scores else 0.0
    
    def _calculate_row_completeness(self, row: pd.Series) -> float:
        """Calculate completeness score for a single row.
        
        Args:
            row: Series representing one row of data
            
        Returns:
            Float between 0.0 and 1.0 representing fraction of fields present
        """
        fields_present = 0
        
        for field in self.REQUIRED_FIELDS:
            if self._is_field_present(row.get(field)):
                fields_present += 1
        
        return fields_present / len(self.REQUIRED_FIELDS)
    
    def _is_field_present(self, value) -> bool:
        """Check if a field value is present and non-empty.
        
        Args:
            value: The field value to check
            
        Returns:
            True if value is not null/NaN and not an empty/whitespace-only string
        """
        # Check for NaN/None
        if pd.isna(value):
            return False
        
        # Check for empty or whitespace-only strings
        if isinstance(value, str):
            return len(value.strip()) > 0
        
        # Other types are considered present
        return True

# Results Quality Assessment

This feature measures the quality of AI categorization results across three dimensions: completeness, confidence, and consistency.

## Architecture

The quality assessment system uses a composable, pluggable architecture:

### Quality Dimensions

#### 1. Completeness Calculator
- **Purpose**: Measures field presence and population
- **Required Fields**: `CategoryAnnotation`, `SubCategoryAnnotation`, `Confidence`
- **Calculation**: Fraction of required fields present and non-empty per row, averaged across all rows
- **Range**: 0.0 (no fields present) to 1.0 (all fields complete)

#### 2. Confidence Calculator
- **Purpose**: Measures AI categorization reliability
- **Input**: `Confidence` column values
- **Calculation**: Weighted average where low confidence scores have higher impact
- **Weighting**:
  - Scores < 0.70: Weight = 3 (highest impact on lowering index)
  - Scores 0.71-0.90: Weight = 2 (medium impact)
  - Scores > 0.90: Weight = 1 (lowest impact)
- **Range**: 0.0 (no valid confidence) to 1.0 (all high confidence)

#### 3. Consistency Calculator
- **Purpose**: Measures categorization consistency within similar transactions
- **Input**: `TransactionDescription`, `CategoryAnnotation`, `SubCategoryAnnotation`
- **Calculation**: Groups transactions by description prefix, measures fraction of groups with uniform categorization
- **Range**: 0.0 (no consistency) to 1.0 (perfect consistency within groups)

### Overall Quality Index
- **Formula**: `(completeness × 0.3) + (confidence × 0.5) + (consistency × 0.2)`
- **Purpose**: Weighted combination of all three dimensions
- **Default Weights**: Completeness (30%), Confidence (50%), Consistency (20%)

## Implementation

### Pluggable Architecture
- `QualityDimensionCalculator` abstract interface for individual dimensions
- `QualityCalculator` abstract interface for complete quality assessment
- `DefaultQualityCalculator` composes all three dimensions via dependency injection
- `SimpleQualityCalculator` provides legacy confidence-only calculation

### Configuration
Quality calculators are pluggable and configurable:
```python
# Use default calculators
calculator = DefaultQualityCalculator()

# Use custom calculators with different weights
calculator = DefaultQualityCalculator(
    completeness_calculator=MyCompletenessCalculator(),
    confidence_calculator=MyConfidenceCalculator(),
    consistency_calculator=MyConsistencyCalculator(),
    completeness_weight=0.4,
    confidence_weight=0.4,
    consistency_weight=0.2
)
```

## Integration

### Command Result
- Quality metrics are returned in `CommandResult.metadata` parameter
- Includes all three dimension scores plus overall quality index
- Calculator name is also stored in metadata

### Pipeline Integration
- `DataPipeline` reads quality metrics after each step
- Updates final pipeline metadata with quality assessment
- Quality metrics are persisted with pipeline execution history

## Outputs

The quality assessment produces:
- **Completeness Score**: Field population quality (0.0-1.0)
- **Confidence Score**: AI reliability assessment (0.0-1.0)
- **Consistency Score**: Categorization uniformity (0.0-1.0)
- **Overall Quality Index**: Weighted combination (0.0-1.0)

All metrics are stored in pipeline metadata for historical analysis and quality monitoring.

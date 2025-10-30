"""Integration tests for quality analysis in complete pipeline workflow."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import (
    DataPipeline,
    QualityAnalysisCommand, PipelineCommand, CommandResult
)
from analyzer.pipeline.quality import SimpleQualityCalculator
from analyzer.pipeline.metadata import MetadataCollector


class MockLoadCommand(PipelineCommand):
    """Mock command that loads categorized data."""
    def process(self, df: pd.DataFrame, context=None) -> CommandResult:
        # Create mock categorized data
        data = pd.DataFrame({
            'CategoryAnnotation': ['Food', 'Transport', 'Utilities', 'Entertainment'],
            'SubCategoryAnnotation': ['Coffee', 'Bus', 'Electric', 'Movie'],
            'Confidence': [0.95, 0.92, 0.88, 0.75],
            'Amount': [5.50, 25.00, 120.00, 15.00]
        })
        return CommandResult(return_code=0, data=data)


def test_quality_analysis_in_complete_pipeline():
    """Test QualityAnalysisCommand as part of complete pipeline workflow."""
    # Create pipeline with quality analysis
    commands = [
        MockLoadCommand(),
        QualityAnalysisCommand(calculator=SimpleQualityCalculator())
    ]
    
    collector = MetadataCollector(pipeline_name="QualityWorkflow")
    pipeline = DataPipeline(commands, collector=collector)
    
    # Run pipeline
    result_df = pipeline.run()
    
    # Verify data flows through
    assert len(result_df) == 4
    assert 'CategoryAnnotation' in result_df.columns
    assert 'Confidence' in result_df.columns
    
    # Verify quality metrics in metadata
    metadata = collector.get_pipeline_metadata()
    metadata_dict = metadata.to_dict()
    
    assert metadata_dict['quality_index'] is not None
    # Average of [0.95, 0.92, 0.88, 0.75] = 0.875
    assert metadata_dict['quality_index'] == pytest.approx(0.875, abs=0.001)


def test_quality_analysis_with_missing_data():
    """Test quality analysis with rows missing category information."""
    
    class MixedDataCommand(PipelineCommand):
        def process(self, df: pd.DataFrame, context=None) -> CommandResult:
            data = pd.DataFrame({
                'CategoryAnnotation': ['Food', None, 'Utilities'],
                'SubCategoryAnnotation': ['Coffee', 'Bus', None],
                'Confidence': [0.95, 0.92, 0.88],
                'Amount': [5.50, 25.00, 120.00]
            })
            return CommandResult(return_code=0, data=data)
    
    commands = [
        MixedDataCommand(),
        QualityAnalysisCommand(calculator=SimpleQualityCalculator())
    ]
    
    collector = MetadataCollector(pipeline_name="QualityMissingData")
    pipeline = DataPipeline(commands, collector=collector)
    
    result_df = pipeline.run()
    
    # Verify data
    assert len(result_df) == 3
    
    # Verify quality reflects missing data
    metadata = collector.get_pipeline_metadata()
    metadata_dict = metadata.to_dict()
    
    # Row 0: 0.95, Row 1: 0 (missing category), Row 2: 0 (missing subcategory)
    # Average: (0.95 + 0 + 0) / 3 = 0.3167
    assert metadata_dict['quality_index'] == pytest.approx(0.3167, abs=0.001)


def test_quality_analysis_captures_all_metrics():
    """Test that full quality metrics are captured in metadata."""
    
    class SimpleDataCommand(PipelineCommand):
        def process(self, df: pd.DataFrame, context=None) -> CommandResult:
            data = pd.DataFrame({
                'CategoryAnnotation': ['Food', 'Transport'],
                'SubCategoryAnnotation': ['Coffee', 'Bus'],
                'Confidence': [0.95, 0.92]
            })
            return CommandResult(return_code=0, data=data)
    
    commands = [
        SimpleDataCommand(),
        QualityAnalysisCommand(calculator=SimpleQualityCalculator())
    ]
    
    collector = MetadataCollector(pipeline_name="QualityMetrics")
    pipeline = DataPipeline(commands, collector=collector)
    
    result_df = pipeline.run()
    
    # Verify metadata structure
    metadata = collector.get_pipeline_metadata()
    assert metadata.quality_index == pytest.approx(0.935, abs=0.001)
    
    # Verify metadata dict includes quality_index
    metadata_dict = metadata.to_dict()
    assert 'quality_index' in metadata_dict
    assert metadata_dict['quality_index'] == pytest.approx(0.935, abs=0.001)
    
    # Verify calculator name was tracked
    assert hasattr(metadata, 'calculator_name')
    assert metadata.calculator_name == 'SimpleQualityCalculator'


def test_quality_analysis_with_low_confidence_data():
    """Test quality analysis with consistently low confidence scores."""
    
    class LowConfidenceCommand(PipelineCommand):
        def process(self, df: pd.DataFrame, context=None) -> CommandResult:
            data = pd.DataFrame({
                'CategoryAnnotation': ['Food', 'Transport', 'Utilities'],
                'SubCategoryAnnotation': ['Coffee', 'Bus', 'Gas'],
                'Confidence': [0.45, 0.52, 0.48]
            })
            return CommandResult(return_code=0, data=data)
    
    commands = [
        LowConfidenceCommand(),
        QualityAnalysisCommand(calculator=SimpleQualityCalculator())
    ]
    
    collector = MetadataCollector(pipeline_name="LowQuality")
    pipeline = DataPipeline(commands, collector=collector)
    
    result_df = pipeline.run()
    
    # Verify low quality is reflected
    metadata = collector.get_pipeline_metadata()
    metadata_dict = metadata.to_dict()
    
    # Average of [0.45, 0.52, 0.48] = 0.4833
    assert metadata_dict['quality_index'] == pytest.approx(0.4833, abs=0.001)
    assert metadata_dict['quality_index'] < 0.5  # Below 50%

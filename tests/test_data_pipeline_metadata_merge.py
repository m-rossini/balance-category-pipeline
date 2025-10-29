"""TDD: Tests for DataPipeline merging metadata_updates from commands."""
import pytest
import pandas as pd
from analyzer.pipeline.pipeline_commands import DataPipeline, QualityAnalysisCommand
from analyzer.pipeline.quality import SimpleQualityCalculator


def test_data_pipeline_merges_metadata_updates_from_command():
    """Test that DataPipeline merges metadata_updates from CommandResult into final metadata."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport'],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Confidence': [0.95, 0.92]
    })
    
    # Create pipeline with quality analysis command
    commands = [QualityAnalysisCommand(calculator=SimpleQualityCalculator())]
    pipeline = DataPipeline(commands=commands)
    
    # Mock metadata repository to capture saved metadata
    class MockRepository:
        def __init__(self):
            self.saved_metadata = None
        
        def save(self, metadata):
            self.saved_metadata = metadata
    
    repository = MockRepository()
    result_df = pipeline.run(initial_df=df, repository=repository)
    
    # Verify result DataFrame is unchanged
    assert result_df.equals(df)
    
    # Verify metadata was saved
    assert repository.saved_metadata is not None
    
    # Verify quality_index was merged into pipeline metadata
    metadata_dict = repository.saved_metadata.to_dict()
    assert 'quality_index' in metadata_dict
    assert metadata_dict['quality_index'] == pytest.approx(0.935, abs=0.001)


def test_data_pipeline_metadata_updates_in_steps():
    """Test that quality metrics from command appear in pipeline metadata."""
    df = pd.DataFrame({
        'CategoryAnnotation': ['Food', 'Transport'],
        'SubCategoryAnnotation': ['Coffee', 'Bus'],
        'Confidence': [0.95, 0.92]
    })
    
    commands = [QualityAnalysisCommand(calculator=SimpleQualityCalculator())]
    pipeline = DataPipeline(commands=commands)
    
    class MockRepository:
        def __init__(self):
            self.saved_metadata = None
        
        def save(self, metadata):
            self.saved_metadata = metadata
    
    repository = MockRepository()
    pipeline.run(initial_df=df, repository=repository)
    
    # Verify pipeline metadata contains quality_index from command
    metadata_dict = repository.saved_metadata.to_dict()
    assert metadata_dict['quality_index'] == pytest.approx(0.935, abs=0.001)
    
    # Verify step still tracks basic info
    steps = metadata_dict['steps']
    assert len(steps) > 0
    quality_step = next((s for s in steps if s['name'] == 'QualityAnalysisCommand'), None)
    assert quality_step is not None
    assert quality_step['input_rows'] == 2
    assert quality_step['output_rows'] == 2

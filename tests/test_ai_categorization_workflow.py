from analyzer.workflows.ai_categorization import get_pipeline
from analyzer.pipeline.pipeline_commands import DataPipeline

def test_ai_categorization_workflow_definition():
    """Test that the ai_categorization workflow is defined and returns a DataPipeline."""
    pipeline = get_pipeline()
    assert isinstance(pipeline, DataPipeline), "The ai_categorization workflow should return a DataPipeline instance."
    assert hasattr(pipeline, 'run') and callable(pipeline.run), "The pipeline should have a callable run method."

def test_ai_categorization_pipeline_commands():
    """Test that the ai_categorization pipeline includes the expected commands in the correct order."""
    from analyzer.pipeline.pipeline_commands import (
        AppendFilesCommand, ApplyFunctionsCommand, MergeTrainnedDataCommand, AIRemoteCategorizationCommand, QualityAnalysisCommand, SaveFileCommand
    )
    
    pipeline = get_pipeline()
    commands = pipeline.commands

    assert len(commands) == 6, "The pipeline should have exactly 6 commands."
    assert isinstance(commands[0], AppendFilesCommand), "The first command should be AppendFilesCommand."
    assert isinstance(commands[1], ApplyFunctionsCommand), "The second command should be ApplyFunctionsCommand."
    assert isinstance(commands[2], MergeTrainnedDataCommand), "The third command should be MergeTrainnedDataCommand."
    assert isinstance(commands[3], AIRemoteCategorizationCommand), "The fourth command should be AIRemoteCategorizationCommand."
    assert isinstance(commands[4], QualityAnalysisCommand), "The fifth command should be QualityAnalysisCommand."
    assert isinstance(commands[5], SaveFileCommand), "The sixth command should be SaveFileCommand."
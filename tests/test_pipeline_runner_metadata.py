"""Test pipeline_runner with metadata collection support."""
import pytest
import argparse
import tempfile
from pathlib import Path
import pandas as pd
from analyzer import pipeline_runner
from analyzer.pipeline.metadata import MetadataRepository


def test_pipeline_runner_accepts_metadata_dir_flag(monkeypatch, caplog):
    """Test that pipeline_runner accepts --metadata-dir flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(
            pipeline_runner, 
            'parse_args', 
            lambda: argparse.Namespace(
                workflow='bank_transaction_analysis', 
                log_level='DEBUG',
                metadata_dir=tmpdir
            )
        )

        from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand, CommandResult
        
        class FakeCommand(PipelineCommand):
            def process(self, df):
                if df is None or df.empty:
                    df = pd.DataFrame([{'id': 1}])
                return CommandResult(return_code=0, data=df)
        
        def fake_get_pipeline():
            return DataPipeline([FakeCommand()])
        
        monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': fake_get_pipeline})
        
        # Should not raise
        pipeline_runner.main()


def test_pipeline_runner_always_saves_metadata(monkeypatch):
    """Test that metadata is always saved for DataPipeline (mandatory)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(
            pipeline_runner, 
            'parse_args', 
            lambda: argparse.Namespace(
                workflow='bank_transaction_analysis', 
                log_level='INFO',
                metadata_dir=tmpdir
            )
        )

        from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand, CommandResult
        
        class FakeCommand(PipelineCommand):
            def process(self, df):
                if df is None or df.empty:
                    df = pd.DataFrame([{'id': i} for i in range(100)])
                return CommandResult(return_code=0, data=df)
        
        # Create a real DataPipeline with fake commands
        def fake_get_pipeline():
            return DataPipeline([FakeCommand()])
        
        monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': fake_get_pipeline})
        
        # Run pipeline_runner
        pipeline_runner.main()
        
        # Verify metadata was saved
        repo = MetadataRepository(storage_path=Path(tmpdir))
        runs = repo.list_runs()
        
        assert len(runs) == 1, f"Metadata should be saved, but found {len(runs)} runs"
        
        loaded_metadata = repo.load(runs[0])
        assert loaded_metadata.pipeline_name == 'bank_transaction_analysis'
        assert len(loaded_metadata.steps) == 1

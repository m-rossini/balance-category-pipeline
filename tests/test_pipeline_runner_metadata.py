"""Test pipeline_runner with metadata collection support."""
import pytest
import argparse
import tempfile
from pathlib import Path
import pandas as pd
from analyzer import pipeline_runner
from analyzer.pipeline.metadata import MetadataRepository


def test_pipeline_runner_accepts_metadata_flag(monkeypatch, caplog):
    """Test that pipeline_runner accepts --collect-metadata flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(
            pipeline_runner, 
            'parse_args', 
            lambda: argparse.Namespace(
                workflow='bank_transaction_analysis', 
                log_level='DEBUG',
                collect_metadata=True,
                metadata_dir=tmpdir
            )
        )

        from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand
        
        class FakeCommand(PipelineCommand):
            def process(self, df):
                if df is None or df.empty:
                    return pd.DataFrame([{'id': 1}])
                return df
        
        def fake_get_pipeline():
            return DataPipeline([FakeCommand()])
        
        monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': fake_get_pipeline})
        
        # Should not raise
        pipeline_runner.main()


def test_pipeline_runner_metadata_disabled_by_default(monkeypatch):
    """Test that metadata collection is disabled by default (backward compatible)."""
    monkeypatch.setattr(
        pipeline_runner, 
        'parse_args', 
        lambda: argparse.Namespace(
            workflow='bank_transaction_analysis', 
            log_level='INFO',
            collect_metadata=False,
            metadata_dir=None
        )
    )

    class FakePipeline:
        def run(self):
            return pd.DataFrame([{'a': 1}])

    monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': lambda: FakePipeline()})
    
    # Should not raise
    pipeline_runner.main()


def test_pipeline_runner_saves_metadata_when_enabled(monkeypatch):
    """Test that metadata is saved when --collect-metadata flag is used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(
            pipeline_runner, 
            'parse_args', 
            lambda: argparse.Namespace(
                workflow='bank_transaction_analysis', 
                log_level='INFO',
                collect_metadata=True,
                metadata_dir=tmpdir
            )
        )

        from analyzer.pipeline.pipeline_commands import DataPipeline, PipelineCommand
        
        class FakeCommand(PipelineCommand):
            def process(self, df):
                if df is None or df.empty:
                    return pd.DataFrame([{'id': i} for i in range(100)])
                return df
        
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

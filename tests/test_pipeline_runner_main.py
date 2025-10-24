import pandas as pd
import argparse
import logging
import pytest

from analyzer import pipeline_runner


def test_pipeline_runner_main_nonempty(monkeypatch, caplog):
    # Monkeypatch parse_args to supply workflow and log level
    monkeypatch.setattr(pipeline_runner, 'parse_args', lambda: argparse.Namespace(workflow='bank_transaction_analysis', log_level='DEBUG'))

    class FakePipeline:
        def run(self):
            return pd.DataFrame([{'a': 1}])

    # Mock the workflow registry to return our fake workflow
    monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': lambda: FakePipeline()})
    caplog.set_level(logging.DEBUG)
    # Should not raise
    pipeline_runner.main()
    # Expect info message about completion
    assert any('Workflow completed' in r.message for r in caplog.records)


def test_pipeline_runner_main_empty(monkeypatch, caplog):
    monkeypatch.setattr(pipeline_runner, 'parse_args', lambda: argparse.Namespace(workflow='bank_transaction_analysis', log_level='DEBUG'))

    class FakePipelineEmpty:
        def run(self):
            return pd.DataFrame()

    # Mock the workflow registry to return our fake workflow
    monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': lambda: FakePipelineEmpty()})
    caplog.set_level(logging.DEBUG)
    pipeline_runner.main()
    # Expect a warning about no data produced
    assert any('No data produced by workflow' in r.message or 'No data produced' in r.message for r in caplog.records)


def test_pipeline_runner_main_invalid_workflow(monkeypatch):
    # Mock parse_args to supply an invalid workflow name
    monkeypatch.setattr(pipeline_runner, 'parse_args', lambda: argparse.Namespace(workflow='nonexistent_workflow', log_level='DEBUG'))

    # Mock the workflow registry to not contain the invalid workflow
    monkeypatch.setattr(pipeline_runner, 'WORKFLOW_REGISTRY', {'bank_transaction_analysis': lambda: None})
    
    # Should raise KeyError when trying to access non-existent workflow
    with pytest.raises(KeyError):
        pipeline_runner.main()

"""Tests for workflows with quality analysis integration."""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from analyzer.workflows.bank_transaction_analysis import get_pipeline as get_bank_pipeline
from analyzer.workflows.minimal_load import get_pipeline as get_minimal_pipeline
from analyzer.workflows.ai_categorization import get_pipeline as get_ai_pipeline


def test_bank_transaction_analysis_has_quality_analysis_command():
    """Test that bank_transaction_analysis workflow includes QualityAnalysisCommand."""
    pipeline = get_bank_pipeline()
    command_names = [type(cmd).__name__ for cmd in pipeline.commands]
    assert 'QualityAnalysisCommand' in command_names, f"QualityAnalysisCommand not found in {command_names}"


def test_bank_transaction_analysis_quality_command_before_save():
    """Test that QualityAnalysisCommand runs before SaveFileCommand."""
    pipeline = get_bank_pipeline()
    command_names = [type(cmd).__name__ for cmd in pipeline.commands]
    
    quality_idx = command_names.index('QualityAnalysisCommand')
    save_idx = command_names.index('SaveFileCommand')
    
    assert quality_idx < save_idx, "QualityAnalysisCommand should run before SaveFileCommand"


def test_minimal_load_has_quality_analysis_command():
    """Test that minimal_load workflow includes QualityAnalysisCommand."""
    pipeline = get_minimal_pipeline()
    command_names = [type(cmd).__name__ for cmd in pipeline.commands]
    assert 'QualityAnalysisCommand' in command_names, f"QualityAnalysisCommand not found in {command_names}"


def test_minimal_load_quality_command_before_save():
    """Test that QualityAnalysisCommand runs before SaveFileCommand in minimal_load."""
    pipeline = get_minimal_pipeline()
    command_names = [type(cmd).__name__ for cmd in pipeline.commands]
    
    quality_idx = command_names.index('QualityAnalysisCommand')
    save_idx = command_names.index('SaveFileCommand')
    
    assert quality_idx < save_idx, "QualityAnalysisCommand should run before SaveFileCommand"


def test_ai_categorization_has_quality_analysis_command():
    """Test that ai_categorization workflow includes QualityAnalysisCommand."""
    pipeline = get_ai_pipeline()
    command_names = [type(cmd).__name__ for cmd in pipeline.commands]
    assert 'QualityAnalysisCommand' in command_names, f"QualityAnalysisCommand not found in {command_names}"


def test_ai_categorization_quality_command_before_save():
    """Test that QualityAnalysisCommand runs before SaveFileCommand in ai_categorization."""
    pipeline = get_ai_pipeline()
    command_names = [type(cmd).__name__ for cmd in pipeline.commands]
    
    quality_idx = command_names.index('QualityAnalysisCommand')
    save_idx = command_names.index('SaveFileCommand')
    
    assert quality_idx < save_idx, "QualityAnalysisCommand should run before SaveFileCommand"


def test_quality_analysis_command_has_reporter():
    """Test that QualityAnalysisCommand in workflows has a reporter configured."""
    pipeline = get_bank_pipeline()
    
    quality_commands = [cmd for cmd in pipeline.commands if type(cmd).__name__ == 'QualityAnalysisCommand']
    assert len(quality_commands) > 0, "No QualityAnalysisCommand found"
    
    quality_cmd = quality_commands[0]
    assert hasattr(quality_cmd, 'reporter'), "QualityAnalysisCommand should have reporter attribute"
    assert quality_cmd.reporter is not None, "Reporter should not be None"

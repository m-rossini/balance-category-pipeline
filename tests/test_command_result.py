"""Tests for CommandResult dataclass."""
import pandas as pd
import pytest
from analyzer.pipeline.command_result import CommandResult


def test_command_result_with_error():
    """Test creating a failed CommandResult with error description."""
    result = CommandResult(
        return_code=-1,
        data=None,
        error={"message": "File not found", "details": "data/missing.csv"}
    )
    
    assert result.return_code == -1
    assert result.data is None
    assert result.error == {"message": "File not found", "details": "data/missing.csv"}


def test_command_result_with_context_updates():
    """Test CommandResult with context updates."""
    df = pd.DataFrame({'col': [1, 2, 3]})
    context_updates = {'new_key': 'new_value', 'count': 42}
    
    result = CommandResult(
        return_code=0,
        data=df,
        context_updates=context_updates
    )
    
    assert result.context_updates == context_updates


def test_command_result_with_metadata_updates():
    """Test CommandResult with metadata updates."""
    df = pd.DataFrame({'col': [1, 2, 3]})
    metadata_updates = {'quality_index': 0.85, 'step_quality': {'completeness': 95}}
    
    result = CommandResult(
        return_code=0,
        data=df,
        metadata_updates=metadata_updates
    )
    
    assert result.metadata_updates == metadata_updates


def test_command_result_complete():
    """Test CommandResult with all fields populated."""
    df = pd.DataFrame({'col': [1, 2, 3]})
    context_updates = {'key': 'value'}
    metadata_updates = {'quality': 0.9}
    
    result = CommandResult(
        return_code=0,
        data=df,
        error=None,
        context_updates=context_updates,
        metadata_updates=metadata_updates
    )
    
    assert result.return_code == 0
    assert result.data is df
    assert result.error is None
    assert result.context_updates == context_updates
    assert result.metadata_updates == metadata_updates


def test_command_result_warning_return_code():
    """Test CommandResult with positive return code (warning)."""
    df = pd.DataFrame({'col': [1, 2, 3]})
    result = CommandResult(
        return_code=1,
        data=df,
        error={"message": "Partial failure", "recovered_rows": 9000}
    )
    
    assert result.return_code == 1  # Positive = warning, continue
    assert result.data is df


def test_command_result_halt_return_code():
    """Test CommandResult with negative return code (halt)."""
    result = CommandResult(
        return_code=-1,
        data=None,
        error={"message": "Critical error - halting pipeline"}
    )
    
    assert result.return_code == -1  # Negative = halt pipeline
    assert result.data is None

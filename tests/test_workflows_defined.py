import inspect
import pytest
from analyzer import pipeline_runner
from analyzer.pipeline.pipeline_commands import DataPipeline


def test_workflow_registry_is_valid():
    """Ensure WORKFLOW_REGISTRY is a dict mapping names to callables returning DataPipeline."""
    registry = getattr(pipeline_runner, 'WORKFLOW_REGISTRY', None)
    assert isinstance(registry, dict), "WORKFLOW_REGISTRY must be a dict"
    assert registry, "WORKFLOW_REGISTRY should not be empty"

    for name, getter in registry.items():
        # Each value should be callable
        assert callable(getter), f"Workflow getter for {name} is not callable"
        # Call the getter and ensure it returns a DataPipeline (or object with run method)
        pipeline = getter()
        assert isinstance(pipeline, DataPipeline), f"Workflow {name} did not return a DataPipeline"
    assert hasattr(pipeline, 'run') and callable(getattr(pipeline, 'run')), f"Pipeline for {name} must have a callable run() method"


if __name__ == '__main__':
    pytest.main([__file__])

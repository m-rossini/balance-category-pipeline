"""Metadata collection and persistence for pipeline and steps."""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StepMetadata:
    """Captures metadata for a single pipeline step."""

    def __init__(
        self,
        name: str,
        input_rows: int,
        output_rows: int,
        duration: Optional[float] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """Initialize step metadata.

        Args:
            name: Name of the step/command
            input_rows: Number of rows input to the step
            output_rows: Number of rows output from the step
            duration: Duration of step execution in seconds
            start_time: When the step started executing
            end_time: When the step finished executing
            parameters: Parameters passed to the step
        """
        self.name = name
        self.input_rows = input_rows
        self.output_rows = output_rows
        self.start_time = start_time
        self.end_time = end_time
        self.parameters = parameters or {}

        # Calculate duration if not provided
        if duration is not None:
            self.duration = duration
        elif start_time and end_time:
            self.duration = (end_time - start_time).total_seconds()
        else:
            self.duration = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "name": self.name,
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "duration": self.duration,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "parameters": self.parameters,
        }


class PipelineMetadata:
    """Captures metadata for an entire pipeline execution."""

    def __init__(
        self,
        pipeline_name: str,
        start_time: datetime,
        end_time: datetime,
        quality_index: Optional[Any] = None,
        context_files: Optional[Dict[str, str]] = None,
    ):
        """Initialize pipeline metadata.

        Args:
            pipeline_name: Name of the pipeline
            start_time: When the pipeline started executing
            end_time: When the pipeline finished executing
            quality_index: Placeholder for quality metrics (optional)
            context_files: Context files used by the pipeline (optional)
        """
        self.pipeline_name = pipeline_name
        self.start_time = start_time
        self.end_time = end_time
        self.run_id = str(uuid.uuid4())
        self.steps: List[StepMetadata] = []
        self.quality_index = quality_index
        self.context_files = context_files
        self.input_rows: Optional[int] = None
        self.output_rows: Optional[int] = None

    @property
    def total_duration(self) -> float:
        """Calculate total duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    def add_step(self, step: StepMetadata) -> None:
        """Add a step's metadata to the pipeline."""
        self.steps.append(step)
        # Update total input/output rows
        if not self.steps or len(self.steps) == 1:
            self.input_rows = step.input_rows
        self.output_rows = step.output_rows

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline metadata to dictionary for serialization."""
        return {
            "pipeline_name": self.pipeline_name,
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration": self.total_duration,
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "quality_index": self.quality_index,
            "context_files": self.context_files,
            "steps": [step.to_dict() for step in self.steps],
        }


class MetadataCollector:
    """Collects metadata during pipeline execution."""

    def __init__(
        self, pipeline_name: str, pipeline_metadata: Optional[PipelineMetadata] = None
    ):
        """Initialize metadata collector.

        Args:
            pipeline_name: Name of the pipeline being executed
            pipeline_metadata: Optional existing PipelineMetadata instance to reuse
        """
        self.pipeline_name = pipeline_name
        self.pipeline_metadata = pipeline_metadata

    def start_pipeline(self) -> None:
        """Start collecting pipeline metadata."""
        # If metadata not provided, create a new one
        if self.pipeline_metadata is None:
            self.pipeline_metadata = PipelineMetadata(
                pipeline_name=self.pipeline_name,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )

    def end_pipeline(self) -> None:
        """End collecting pipeline metadata."""
        if self.pipeline_metadata:
            self.pipeline_metadata.end_time = datetime.now()

    def track_step(self, step: StepMetadata) -> None:
        """Track a step's metadata.

        Args:
            step: The StepMetadata to track
        """
        if self.pipeline_metadata:
            self.pipeline_metadata.add_step(step)

    def get_pipeline_metadata(self) -> PipelineMetadata:
        """Get the collected pipeline metadata.

        Returns:
            The PipelineMetadata instance
        """
        return self.pipeline_metadata

    def __enter__(self):
        """Context manager entry - start pipeline collection."""
        self.start_pipeline()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - end pipeline collection."""
        self.end_pipeline()
        return False


class MetadataRepository:
    """Manages persistence of pipeline metadata."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize metadata repository.

        Args:
            storage_path: Where to store metadata files. Defaults to .metadata in user home.
        """
        if storage_path is None:
            storage_path = Path.home() / ".metadata" / "pipelines"

        logging.info(f"[MetadataRepository] Using storage path: {storage_path}")

        self.storage_path = Path(storage_path)

    def save(self, pipeline_metadata: PipelineMetadata) -> str:
        """Save pipeline metadata to storage.

        Args:
            pipeline_metadata: The metadata to save

        Returns:
            The run_id of the saved metadata
        """
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Save to file using run_id as filename
        file_path = self.storage_path / f"{pipeline_metadata.run_id}.json"

        with open(file_path, "w") as f:
            json.dump(pipeline_metadata.to_dict(), f, indent=2)

        return pipeline_metadata.run_id

    def load(self, run_id: str) -> Optional[PipelineMetadata]:
        """Load pipeline metadata from storage.

        Args:
            run_id: The run_id to load

        Returns:
            The loaded PipelineMetadata or None if not found
        """
        file_path = self.storage_path / f"{run_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)

        # Reconstruct PipelineMetadata from dict
        pipeline = PipelineMetadata(
            pipeline_name=data["pipeline_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            quality_index=data.get("quality_index"),
        )
        pipeline.run_id = data["run_id"]
        pipeline.input_rows = data.get("input_rows")
        pipeline.output_rows = data.get("output_rows")

        # Reconstruct steps
        for step_data in data.get("steps", []):
            step = StepMetadata(
                name=step_data["name"],
                input_rows=step_data["input_rows"],
                output_rows=step_data["output_rows"],
                duration=step_data.get("duration"),
                start_time=(
                    datetime.fromisoformat(step_data["start_time"])
                    if step_data.get("start_time")
                    else None
                ),
                end_time=(
                    datetime.fromisoformat(step_data["end_time"])
                    if step_data.get("end_time")
                    else None
                ),
                parameters=step_data.get("parameters", {}),
            )
            pipeline.add_step(step)

        return pipeline

    def list_runs(self) -> List[str]:
        """List all saved run IDs.

        Returns:
            List of run_ids in storage
        """
        if not self.storage_path.exists():
            return []

        runs = []
        for file_path in self.storage_path.glob("*.json"):
            run_id = file_path.stem
            runs.append(run_id)

        return sorted(runs)

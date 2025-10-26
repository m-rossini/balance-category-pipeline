"""Metadata collection and persistence for pipeline and steps."""
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


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
        parameters: Optional[Dict[str, Any]] = None
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
            "parameters": self.parameters
        }


class PipelineMetadata:
    """Captures metadata for an entire pipeline execution."""
    
    def __init__(
        self,
        pipeline_name: str,
        start_time: datetime,
        end_time: datetime,
        quality_index: Optional[Any] = None
    ):
        """Initialize pipeline metadata.
        
        Args:
            pipeline_name: Name of the pipeline
            start_time: When the pipeline started executing
            end_time: When the pipeline finished executing
            quality_index: Placeholder for quality metrics (optional)
        """
        self.pipeline_name = pipeline_name
        self.start_time = start_time
        self.end_time = end_time
        self.run_id = str(uuid.uuid4())
        self.steps: List[StepMetadata] = []
        self.quality_index = quality_index
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
            "steps": [step.to_dict() for step in self.steps]
        }


class MetadataCollector:
    """Collects metadata during pipeline execution."""
    
    def __init__(self, pipeline_name: str):
        """Initialize metadata collector.
        
        Args:
            pipeline_name: Name of the pipeline being executed
        """
        self.pipeline_name = pipeline_name
        self.pipeline_metadata: Optional[PipelineMetadata] = None
    
    def start_pipeline(self) -> None:
        """Start collecting pipeline metadata."""
        self.pipeline_metadata = PipelineMetadata(
            pipeline_name=self.pipeline_name,
            start_time=datetime.now(),
            end_time=datetime.now()
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



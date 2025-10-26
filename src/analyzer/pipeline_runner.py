import argparse
import logging
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from analyzer.pipeline.pipeline_commands import (
    DataPipeline, AppendFilesCommand, CleanDataCommand,
    MergeFilesCommand, SaveFileCommand
)
from analyzer.pipeline.metadata import MetadataCollector, MetadataRepository
from analyzer.workflows.bank_extract_clean import bank_extract_clean

# Import workflow definitions
from analyzer.workflows import bank_transaction_analysis, minimal_load, ai_categorization

# Workflow registry mapping names to get_pipeline functions
WORKFLOW_REGISTRY = {
    'bank_transaction_analysis': bank_transaction_analysis.get_pipeline,
    'minimal_load': minimal_load.get_pipeline,
    'ai_categorization': ai_categorization.get_pipeline,
}

def parse_args():
    parser = argparse.ArgumentParser(description="Run a data processing workflow.")
    parser.add_argument('--workflow', default='bank_transaction_analysis', 
                       choices=list(WORKFLOW_REGISTRY.keys()),
                       help='Workflow to run')
    parser.add_argument('--log-level', default='INFO', help='Logging level (e.g., DEBUG, INFO, WARNING)')
    parser.add_argument('--metadata-dir', default=None, help='Directory to store metadata (defaults to ~/.metadata/pipelines)')
    return parser.parse_args()

# --- CLI ---
def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    
    # Setup metadata collection (mandatory)
    metadata_dir = getattr(args, 'metadata_dir', None)
    metadata_path = Path(metadata_dir) if metadata_dir else None
    repository = MetadataRepository(storage_path=metadata_path)
    
    # Create PipelineMetadata instance and inject into DataPipeline's collector
    from analyzer.pipeline.metadata import PipelineMetadata
    pipeline_metadata = PipelineMetadata(
        pipeline_name=args.workflow,
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    
    pipeline = WORKFLOW_REGISTRY[args.workflow]()
    
    # For DataPipeline, inject the metadata into its auto-created collector
    # Metadata collection is mandatory for all DataPipeline runs
    if isinstance(pipeline, DataPipeline):
        pipeline.collector.pipeline_metadata = pipeline_metadata
    
    logging.debug(f"[pipeline_runner] Workflow context: {getattr(pipeline, 'context', None)}")
    start_time = time.time()
    
    # Run pipeline - DataPipeline always has a collector and saves metadata
    if isinstance(pipeline, DataPipeline):
        result_df = pipeline.run(repository=repository)
    else:
        result_df = pipeline.run()
    
    elapsed = time.time() - start_time
    
    if isinstance(result_df, pd.DataFrame) and result_df.empty:
        logging.warning("[pipeline_runner]No data produced by workflow.")
    else:
        logging.info(f"[pipeline_runner] Workflow completed. Output rows: {len(result_df) if isinstance(result_df, pd.DataFrame) else 'N/A'}, total time: {elapsed:.2f} seconds")
    
    # Log metadata info (always collected for DataPipeline)
    if isinstance(pipeline, DataPipeline):
        metadata = pipeline.collector.get_pipeline_metadata()
        if metadata:
            logging.info(f"[pipeline_runner] Metadata saved. Run ID: {metadata.run_id}")

if __name__ == "__main__":
    main()

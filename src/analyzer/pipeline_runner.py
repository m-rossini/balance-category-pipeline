import argparse
import logging
import pandas as pd
import time
from analyzer.pipeline.pipeline_commands import (
    DataPipeline, AppendFilesCommand, CleanDataCommand,
    MergeFilesCommand, SaveFileCommand
)
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
    return parser.parse_args()

# --- CLI ---
def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    pipeline = WORKFLOW_REGISTRY[args.workflow]()
    logging.debug(f"[pipeline_runner] Workflow context: {getattr(pipeline, 'context', None)}")
    start_time = time.time()
    result_df = pipeline.run()
    elapsed = time.time() - start_time
    if isinstance(result_df, pd.DataFrame) and result_df.empty:
        logging.warning("[pipeline_runner]No data produced by workflow.")
    else:
        logging.info(f"[pipeline_runner] Workflow completed. Output rows: {len(result_df) if isinstance(result_df, pd.DataFrame) else 'N/A'}, total time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()

from analyzer.pipeline.pipeline_commands import (
    DataPipeline, AppendFilesCommand, CleanDataCommand,
    AIRemoteCategorizationCommand, QualityAnalysisCommand, SaveFileCommand
)
from analyzer.pipeline.quality import SimpleQualityCalculator
from analyzer.workflows.bank_extract_clean import bank_extract_clean
import os

def get_pipeline():
    """Define the unified AI categorization workflow with configurable parameters."""
    context = {
        "categories": "context/candidate_categories.json",
        "typecode": "context/transaction_type_codes.json"
    }
    
    # Configurable parameters via environment variables
    service_url = os.getenv('AI_SERVICE_URL', 'http://perez:5000/balance/')  # Default service URL
    
    # Generate output path based on service
    service_name = service_url.replace('http://', '').replace('https://', '').replace('/', '_').replace(':', '_')
    output_path = f'data/output/ai_categorized_{service_name}_bos.csv'
    
    # Mirror the bank transaction analysis pipeline but insert the AI remote
    # categorization step before saving the annotated output.
    from analyzer.pipeline.pipeline_commands import MergeFilesCommand

    return DataPipeline(
        [
            AppendFilesCommand(
                input_dir='data/extratos/demo/',
                file_glob='*.csv'
            ),
            CleanDataCommand(
                functions=[bank_extract_clean]
            ),
            MergeFilesCommand(
                input_file='data/training/factoids.csv',
                on_columns=['TransactionNumber']
            ),
            AIRemoteCategorizationCommand(
                service_url=service_url,
                method="POST",
                headers={"Authorization": os.getenv('AI_SERVICE_API_KEY', '')},
                data={"transactions": []}  # Will be populated with transaction data
            ),
            QualityAnalysisCommand(calculator=SimpleQualityCalculator()),
            SaveFileCommand(
                output_path=output_path,
                save_empty=False
            )
        ],
        context=context
    )
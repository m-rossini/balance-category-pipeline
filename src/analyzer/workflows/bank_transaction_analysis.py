from analyzer.pipeline.pipeline_commands import (
    DataPipeline, AppendFilesCommand, CleanDataCommand,
    MergeFilesCommand, SaveFileCommand, QualityAnalysisCommand
)
from analyzer.workflows.bank_extract_clean import bank_extract_clean
from analyzer.workflows.log_quality_reporter import LogQualityReporter

def get_pipeline():
    """Define the bank transaction analysis pipeline."""
    context = {
        "categories": "context/candidate_categories.json",
        "typecode": "context/transaction_type_codes.json"
    }
    return DataPipeline([
        AppendFilesCommand(
            input_dir='data/extratos/bank_bos',
            file_glob='*.csv',
            context=context
        ),
        CleanDataCommand(
            functions=[bank_extract_clean],
            context=context
        ),
        MergeFilesCommand(
            input_file='data/training/factoids.csv',
            on_columns=['TransactionNumber'],
            context=context
        ),
        QualityAnalysisCommand(
            columns=['CategoryAnnotation', 'SubCategoryAnnotation', 'Confidence'],
            reporter=LogQualityReporter(),
            context=context
        ),
        SaveFileCommand(
            output_path='data/output/annotated_bos.csv',
            save_empty=False,
            context=context
        )
    ])
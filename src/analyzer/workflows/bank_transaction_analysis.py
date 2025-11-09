from analyzer.pipeline.pipeline_commands import (
    DataPipeline, AppendFilesCommand, CleanDataCommand,
    MergeTrainnedDataCommand, SaveFileCommand
)
from analyzer.workflows.bank_extract_clean import bank_extract_clean

def get_pipeline():
    """Define the bank transaction analysis pipeline."""
    context = {
        "categories": "context/candidate_categories.json",
        "typecode": "context/transaction_type_codes.json"
    }
    return DataPipeline(
        [
            AppendFilesCommand(
                input_dir='data/extratos/bank_bos',
                file_glob='*.csv'
            ),
            CleanDataCommand(
                functions=[bank_extract_clean]
            ),
            MergeTrainnedDataCommand(
                input_file='data/training/factoids.csv',
                on_columns=['TransactionNumber']
            ),
            SaveFileCommand(
                output_path='data/output/annotated_bos.csv',
                save_empty=False
            )
        ],
        context=context
    )
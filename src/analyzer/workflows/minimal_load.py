from analyzer.pipeline.pipeline_commands import (AppendFilesCommand,
                                                 DataPipeline, SaveFileCommand)


def get_pipeline():
    """Define a minimal pipeline that just loads and saves bank data."""
    return DataPipeline(
        [
            AppendFilesCommand(input_dir="data/extratos/bank_bos", file_glob="*.csv"),
            SaveFileCommand(output_path="data/output/raw_bos.csv", save_empty=False),
        ]
    )

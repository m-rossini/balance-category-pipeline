import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
import logging
import time
from typing import Dict, Any, Optional, List
import os
import json
import requests

from .categorization_types import (
    CategorizationContext, Transaction, CategorizationPayload,
    Category, CategorizationSuccess, CategorizationFailure, CategorizationResult
)
from .command_result import CommandResult

# Decorator-based command registry
COMMAND_REGISTRY = {}
def register_command(cls):
    COMMAND_REGISTRY[cls.__name__] = cls
    return cls

class PipelineCommand(ABC):
    @abstractmethod
    def process(self, df: pd.DataFrame) -> CommandResult:
        pass

@register_command
class MergeFilesCommand(PipelineCommand):
    def __init__(self, input_dir=None, input_file=None, on_columns: Optional[List[str]] = None, file_filter=None, file_glob='*', context: Optional[Dict[str, Any]] = None):
        # Two modes:
        # - append mode: provide input_dir and file_glob to concatenate multiple files
        # - merge mode: provide an incoming df and an input_file + on_columns to merge with
        self.input_dir = input_dir
        self.input_file = input_file
        self.on_columns = on_columns or []
        self.file_filter = file_filter or (lambda f: True)
        self.file_glob = file_glob
        self.context = context or {}

    def process(self, df=None) -> CommandResult:
        if df is None or not self.input_file:
            return CommandResult(return_code=-1, data=None, error={"message": "Missing input DataFrame or input file"})

        try:
            logging.debug(f"[MergeFilesCommand] Merging with {self.input_file} on {self.on_columns}")
            other = pd.read_csv(self.input_file, usecols=['TransactionNumber', 'CategoryAnnotation', 'SubCategoryAnnotation', 'Confidence'])
            common = self.on_columns or ['TransactionNumber']

            # Perform the merge
            merged = pd.merge(df, other, how='left', on=common, suffixes=(None, '_trained'))

            # Prepare numeric confidence series for comparison (trained and original)
            trained_conf = pd.to_numeric(merged.get('Confidence_trained'), errors='coerce') if 'Confidence_trained' in merged.columns else pd.Series([float('nan')] * len(merged), index=merged.index)
            orig_conf = pd.to_numeric(merged.get('Confidence'), errors='coerce') if 'Confidence' in merged.columns else pd.Series([float('nan')] * len(merged), index=merged.index)

            # For category/subcategory: replace when trained value exists and either
            # - original category/subcategory is empty/whitespace OR
            # - original confidence is missing OR smaller than trained confidence
            for col in ["CategoryAnnotation", "SubCategoryAnnotation"]:
                trained_col = f"{col}_trained"
                if trained_col in merged.columns:
                    trained = merged[trained_col]
                    orig = merged[col] if col in merged.columns else pd.Series([None] * len(merged), index=merged.index)
                    empty_orig = orig.isna() | (orig.astype(str).str.strip() == "")
                    # Treat missing original confidence as replaceable
                    better_conf = trained_conf.notna() & (orig_conf.isna() | (orig_conf < trained_conf))
                    mask = trained.notna() & (empty_orig | better_conf)
                    if mask.any():
                        merged.loc[mask, col] = trained.loc[mask]
                    merged.drop(columns=[trained_col], inplace=True)

            # For Confidence: replace when trained confidence exists and is greater than original (or original missing)
            if 'Confidence_trained' in merged.columns:
                mask_conf = trained_conf.notna() & (orig_conf.isna() | (orig_conf < trained_conf))
                if mask_conf.any():
                    merged.loc[mask_conf, 'Confidence'] = trained_conf.loc[mask_conf]
                merged.drop(columns=['Confidence_trained'], inplace=True)

            logging.info(f"[MergeFilesCommand] Merge completed. Resulting rows: {len(merged)}")
            return CommandResult(return_code=0, data=merged)
        except Exception as e:
            return CommandResult(return_code=-1, data=None, error={"message": str(e)})

@register_command
class CleanDataCommand(PipelineCommand):
    def __init__(self, functions=None, context: Optional[Dict[str, Any]] = None):
        # accept context for compatibility with workflows
        self.context = context or {}
        self.functions = functions or [CleanDataCommand.default_clean]
    
    def process(self, df: pd.DataFrame) -> CommandResult:
        logging.debug(f"[CleanDataCommand] Starting cleaning. Input shape: {df.shape}")
        if df.empty:
            logging.warning("No data to clean.")
            return CommandResult(return_code=0, data=df)
        for fn in self.functions:
            df = fn(df)
        logging.debug(f"[CleanDataCommand] Cleaned DataFrame shape: {df.shape}")
        logging.info(f"Cleaned data: {len(df)} rows remain after cleaning.")
        return CommandResult(return_code=0, data=df)
    
    @staticmethod
    def default_clean(df: pd.DataFrame) -> pd.DataFrame:
        return df


@register_command
class AppendFilesCommand(PipelineCommand):
    """Read multiple CSV files from a directory (or a provided iterable of files)
    and return a concatenated pandas DataFrame.

    This matches the usage in workflows where the command is constructed with
    `input_dir`, `file_glob` and optional `file_filter` and `context`.
    """
    def __init__(self, input_dir=None, file_glob='*.csv', file_filter=None, input_files=None, context: Optional[Dict[str, Any]] = None):
        self.input_dir = input_dir
        self.file_glob = file_glob
        self.file_filter = file_filter or (lambda f: True)
        self.input_files = input_files
        self.context = context or {}
        logging.debug(f"[AppendFilesCommand] Initialized with input_dir={self.input_dir}, file_glob={self.file_glob}, input_files={self.input_files}")  

    def process(self, df: Optional[pd.DataFrame] = None) -> CommandResult:
        logging.debug(f"[AppendFilesCommand] Starting append. input_dir={self.input_dir} file_glob={self.file_glob}")

        files = []
        if self.input_files is not None:
            files = [Path(f) for f in self.input_files]
        elif self.input_dir is not None:
            logging.debug(f"[AppendFilesCommand] Listing files in directory: {self.input_dir} with glob: {self.file_glob}")
            files = [f for f in Path(self.input_dir).glob(self.file_glob) if self.file_filter(f)]
        else:
            return CommandResult(return_code=-1, data=None, error={"message": "No input_dir or input_files provided"})

        logging.debug(f"[AppendFilesCommand] Found {len(files)} files before filtering.")
        if not files:
            return CommandResult(return_code=-1, data=None, error={"message": "No files found"})

        # Sort to reverse the order: latest files first
        files_sorted = sorted(files, key=lambda x: x.name, reverse=True)
        dfs = []
        for f in files_sorted:
            try:
                logging.debug(f"[AppendFilesCommand] Reading file {f}")
                df_piece = pd.read_csv(f)
                dfs.append(df_piece)
            except Exception as e:
                logging.error(f"[AppendFilesCommand] Failed to read {f}: {e}")
        
        if not dfs:
            return CommandResult(return_code=-1, data=None, error={"message": "No readable files"})

        combined = pd.concat(dfs, ignore_index=True)
        logging.info(f"[AppendFilesCommand] Appended {len(dfs)} files, resulting rows: {len(combined)}")
        return CommandResult(return_code=0, data=combined)

@register_command
class SaveFileCommand(PipelineCommand):
    def __init__(self, output_path, save_empty: bool = True, context: Optional[Dict[str, Any]] = None):
        self.output_path = Path(output_path)
        self.save_empty = save_empty
        self.context = context or {}
    
    def process(self, df: pd.DataFrame) -> CommandResult:
        try:
            if df.empty and not self.save_empty:
                return CommandResult(return_code=0, data=df)
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(str(self.output_path), index=False)
            logging.info(f"[SaveFileCommand] Saved to {self.output_path} ({len(df)}) rows")
            return CommandResult(return_code=0, data=df)
        except Exception as e:
            return CommandResult(return_code=-1, data=None, error={"message": str(e)})


@register_command
class AIRemoteCategorizationCommand(PipelineCommand):
    def __init__(self, service_url, method="POST", headers=None, data=None, context=None, batch_size=50, max_errors=10, impl="fixed"):
        self.service_url = service_url
        self.method = method.upper()
        self.headers = headers or {}
        self.data = data or {}
        self.context = context or {}
        self.batch_size = batch_size
        self.max_errors = max_errors
        self.impl = impl

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process DataFrame by calling remote categorization API in batches."""
        if len(df) == 0:
            return df

        logging.info(f"[AIRemoteCategorizationCommand] Processing {len(df)} records in batches of {self.batch_size}")

        # Step 1: Load context
        context_list = self._load_context()

        # Step 2: Process batches
        error_count = 0
        for start in range(0, len(df), self.batch_size):
            if error_count >= self.max_errors:
                logging.error(f"[AIRemoteCategorizationCommand] Stopping after {error_count} errors (max: {self.max_errors})")
                break
            
            end = min(start + self.batch_size, len(df))
            batch_df = df.iloc[start:end]
            
            # Step 3: Build and send batch
            transactions = self._build_transactions(batch_df)
            payload = {"context": context_list, "transactions": transactions}
            
            # Step 4: Call API
            response_data = self._call_api(payload, start, end)
            
            # Step 5: Merge results
            if response_data:
                df = self._merge_results(df, response_data)
            else:
                error_count += 1

        return df

    def _load_context(self) -> List[Dict]:
        """Load all context files (driver method)."""
        context_list = []
        context_list.extend(self._load_context_file('categories'))
        context_list.extend(self._load_context_file('typecode'))
        return context_list

    def _load_context_file(self, context_key: str) -> List[Dict]:
        """Load a context file from the context dictionary.
        
        Args:
            context_key: The key in self.context dict (e.g., 'categories', 'typecode')
            
        Returns:
            List containing the loaded JSON data, or empty list if not available
        """
        if not self.context or context_key not in self.context:
            return []
        
        try:
            file_path = self.context[context_key]
            with open(file_path, 'r') as f:
                context_data = json.load(f)
                logging.debug(f"[AIRemoteCategorizationCommand] Loaded {context_key} from {file_path}")
                return [context_data]
        except Exception as e:
            logging.error(f"[AIRemoteCategorizationCommand] Could not load {context_key}: {e}")
            return []

    def _build_transactions(self, batch_df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame batch to transaction list."""
        # Select and rename columns for API payload
        selected_df = batch_df[['TransactionDescription', 'TransactionValue', 'TransactionDate', 'TransactionType']].copy()
        selected_df.columns = ['description', 'amount', 'date', 'type']
        
        # Add id column based on index
        selected_df['id'] = selected_df.index.astype(str)
        
        # Convert to list of dicts with proper field order
        transactions = selected_df[['id', 'description', 'amount', 'date', 'type']].to_dict(orient='records')
        logging.debug(f"[AIRemoteCategorizationCommand] Built {len(transactions)} transactions from batch of {len(batch_df)} rows")
        return transactions

    def _call_api(self, payload: Dict, batch_start: int, batch_end: int) -> Optional[Dict]:
        """Call remote API with payload and return response data."""
        try:
            logging.debug(f"[AIRemoteCategorizationCommand] Sending batch {batch_start+1}-{batch_end}")
            
            response = requests.post(
                self.service_url,
                json=payload,
                params={"impl": self.impl},
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            
            logging.info(f"[AIRemoteCategorizationCommand] Batch {batch_start+1}-{batch_end} successful")
            return response_data
            
        except Exception as e:
            error_msg = str(e)
            # Append response body if available
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" | Response: {e.response.text}"
            logging.error(f"[AIRemoteCategorizationCommand] Batch {batch_start+1}-{batch_end} failed: {error_msg}")
            return None

    def _merge_results(self, df: pd.DataFrame, response_data: Dict) -> pd.DataFrame:
        """Apply categorization results to DataFrame and return updated copy.
        
        Pure function: returns a new DataFrame without mutating the input.
        """
        if response_data.get('code') != 'SUCCESS':
            return df
        
        # Create a copy to avoid mutating the input
        result_df = df.copy()
        
        for item in response_data.get('items', []):
            item_id = int(item.get('id'))
            category_data = item.get('category')
            
            if category_data is None:
                continue
            
            result_df.loc[item_id, 'CategoryAnnotation'] = category_data.get('category')
            result_df.loc[item_id, 'SubCategoryAnnotation'] = category_data.get('subcategory')
            result_df.loc[item_id, 'Confidence'] = category_data.get('confidence')
            
            if 'transaction_number' in category_data:
                result_df.loc[item_id, 'TransactionNumber'] = category_data.get('transaction_number')
        
        return result_df


class DataPipeline:
    def __init__(self, commands, collector=None):
        self.commands = commands
        # Always ensure we have a collector
        if collector is None:
            from analyzer.pipeline.metadata import MetadataCollector
            self.collector = MetadataCollector(pipeline_name="DataPipeline")
        else:
            self.collector = collector
        
    def run(self, initial_df=None, repository=None):
        df = initial_df
        
        # Always start pipeline collection (collector is always present)
        self.collector.start_pipeline()
        
        for command in self.commands:
            logging.debug(f"[DataPipeline] Running step: {command.__class__.__name__}")
            start = time.time()
            input_rows = len(df) if isinstance(df, pd.DataFrame) else 0
            
            result = command.process(df)
            
            # Handle CommandResult
            if isinstance(result, CommandResult):
                # Check return code - halt on negative codes
                if result.return_code < 0:
                    logging.error(f"[DataPipeline] Command {command.__class__.__name__} failed with return_code={result.return_code}: {result.error}")
                    # Return empty DataFrame to indicate failure
                    return pd.DataFrame()
                df = result.data
            else:
                # Fallback for legacy DataFrame returns
                df = result
            
            output_rows = len(df) if isinstance(df, pd.DataFrame) else 0
            elapsed = time.time() - start
            logging.debug(f"[DataPipeline] Step {command.__class__.__name__} completed in {elapsed:.4f} seconds")
            
            # Track step metadata (collector always present)
            from analyzer.pipeline.metadata import StepMetadata
            step_metadata = StepMetadata(
                name=command.__class__.__name__,
                input_rows=input_rows,
                output_rows=output_rows,
                duration=elapsed,
                parameters={}
            )
            self.collector.track_step(step_metadata)
        
        # Always end collection (collector is always present)
        self.collector.end_pipeline()
        
        # Save metadata if repository provided
        if repository:
            metadata = self.collector.get_pipeline_metadata()
            repository.save(metadata)
        
        return df

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

# Decorator-based command registry
COMMAND_REGISTRY = {}
def register_command(cls):
    COMMAND_REGISTRY[cls.__name__] = cls
    return cls

class PipelineCommand(ABC):
    @abstractmethod
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
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

    def process(self, df=None):
        if df is None or not self.input_file:
            logging.error("[MergeFilesCommand] Missing input DataFrame or input file.")
            return pd.DataFrame()

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
            return merged
        except Exception as e:
            logging.error(f"[MergeFilesCommand] Failed to merge: {e}")
            return df

@register_command
class CleanDataCommand(PipelineCommand):
    def __init__(self, functions=None, context: Optional[Dict[str, Any]] = None):
        # accept context for compatibility with workflows
        self.context = context or {}
        self.functions = functions or [CleanDataCommand.default_clean]
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.debug(f"[CleanDataCommand] Starting cleaning. Input shape: {df.shape}")
        if df.empty:
            logging.warning("No data to clean.")
            return df
        for fn in self.functions:
            df = fn(df)
        logging.debug(f"[CleanDataCommand] Cleaned DataFrame shape: {df.shape}")
        logging.info(f"Cleaned data: {len(df)} rows remain after cleaning.")
        return df
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

    def process(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        logging.debug(f"[AppendFilesCommand] Starting append. input_dir={self.input_dir} file_glob={self.file_glob}")

        files = []
        if self.input_files is not None:
            files = [Path(f) for f in self.input_files]
        elif self.input_dir is not None:
            logging.debug(f"[AppendFilesCommand] Listing files in directory: {self.input_dir} with glob: {self.file_glob}")
            files = [f for f in Path(self.input_dir).glob(self.file_glob) if self.file_filter(f)]
        else:
            logging.error("[AppendFilesCommand] No input_dir or input_files provided.")
            return pd.DataFrame()

        logging.debug(f"[AppendFilesCommand] Found {len(files)} files before filtering.")
        if not files:
            logging.warning(f"[AppendFilesCommand] No files found (input_dir={self.input_dir}, input_files={self.input_files}).")
            return pd.DataFrame()

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
            logging.error("[AppendFilesCommand] No readable files produced DataFrames.")
            return pd.DataFrame()

        combined = pd.concat(dfs, ignore_index=True)
        logging.info(f"[AppendFilesCommand] Appended {len(dfs)} files, resulting rows: {len(combined)}")
        return combined

@register_command
class SaveFileCommand(PipelineCommand):
    def __init__(self, output_path, save_empty: bool = True, context: Optional[Dict[str, Any]] = None):
        self.output_path = Path(output_path)
        self.save_empty = save_empty
        self.context = context or {}
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.debug(f"[SaveFileCommand] Saving DataFrame with shape: {df.shape} to {self.output_path}")
        if df.empty and not self.save_empty:
            logging.info(f"[SaveFileCommand] DataFrame empty and save_empty=False; skipping save to {self.output_path}")
            return df
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(str(self.output_path), index=False)
        logging.info(f"Saved output to {self.output_path} ({len(df)} rows)")
        return df


@register_command
class AIRemoteCategorizationCommand(PipelineCommand):
    def __init__(self, service_url, method="POST", headers=None, data=None, context=None, batch_size=50, max_errors=10):
        self.service_url = service_url
        self.method = method.upper()
        self.headers = headers or {}
        self.data = data or {}
        self.context = context or {}
        self.batch_size = batch_size
        self.max_errors = max_errors

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
                self._merge_results(df, response_data)
            else:
                error_count += 1

        return df

    def _load_context(self) -> List[Dict]:
        """Load all context files (driver method)."""
        context_list = []
        context_list.extend(self._load_categories())
        context_list.extend(self._load_transaction_codes())
        return context_list

    def _load_categories(self) -> List[Dict]:
        """Load categories context from file."""
        if not self.context or 'categories' not in self.context:
            return []
        
        try:
            with open(self.context['categories'], 'r') as f:
                categories_data = json.load(f)
                logging.debug(f"[AIRemoteCategorizationCommand] Loaded categories from {self.context['categories']}")
                return [categories_data]
        except Exception as e:
            logging.warning(f"[AIRemoteCategorizationCommand] Could not load categories: {e}")
            return [{"categories": "Unable to load"}]

    def _load_transaction_codes(self) -> List[Dict]:
        """Load transaction type codes context from file."""
        if not self.context or 'typecode' not in self.context:
            return []
        
        try:
            with open(self.context['typecode'], 'r') as f:
                typecode_data = json.load(f)
                logging.debug(f"[AIRemoteCategorizationCommand] Loaded transaction codes from {self.context['typecode']}")
                return [typecode_data]
        except Exception as e:
            logging.warning(f"[AIRemoteCategorizationCommand] Could not load transaction codes: {e}")
            return [{"transaction_codes": "Unable to load"}]

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
                params={"impl": "fixed"},
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            
            logging.info(f"[AIRemoteCategorizationCommand] Batch {batch_start+1}-{batch_end} successful")
            return response_data
            
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg += f" | Response: {e.response.text}"
                except:
                    pass
            logging.error(f"[AIRemoteCategorizationCommand] Batch {batch_start+1}-{batch_end} failed: {error_msg}")
            return None

    def _merge_results(self, df: pd.DataFrame, response_data: Dict) -> None:
        """Apply categorization results to DataFrame."""
        if response_data.get('code') != 'SUCCESS':
            return
        
        for item in response_data.get('items', []):
            item_id = int(item.get('id'))
            category_data = item.get('category')
            
            if category_data is None:
                continue
            
            df.loc[item_id, 'CategoryAnnotation'] = category_data.get('category')
            df.loc[item_id, 'SubCategoryAnnotation'] = category_data.get('subcategory')
            df.loc[item_id, 'Confidence'] = category_data.get('confidence')
            
            if 'transaction_number' in category_data:
                df.loc[item_id, 'TransactionNumber'] = category_data.get('transaction_number')


class DataPipeline:
    def __init__(self, commands):
        self.commands = commands
    def run(self, initial_df=None):
        df = initial_df
        for command in self.commands:
            logging.debug(f"[DataPipeline] Running step: {command.__class__.__name__}")
            start = time.time()
            df = command.process(df)
            elapsed = time.time() - start
            logging.debug(f"[DataPipeline] Step {command.__class__.__name__} completed in {elapsed:.4f} seconds")
        return df

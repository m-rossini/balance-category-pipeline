"""CommandResult dataclass for pipeline command return values."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd


@dataclass
class CommandResult:
    """Result object returned by pipeline commands.

    Attributes:
        return_code: 0 for success, negative to halt pipeline, positive to warn and continue
        data: The DataFrame to pass to next command (None if error and halting)
        error: Error details dict if command failed
        context_updates: New context keys/values to merge into pipeline context
        metadata_updates: Metadata keys/values to merge into pipeline metadata
    """

    return_code: int
    data: Optional[pd.DataFrame] = None
    error: Optional[Dict[str, Any]] = None
    context_updates: Optional[Dict[str, Any]] = None
    metadata_updates: Optional[Dict[str, Any]] = None

from dataclasses import dataclass, asdict
from typing import List, Optional, Union

@dataclass
class CategorizationContext:
    categories: str
    typecode: str
    # Add other context fields as needed

@dataclass
class Transaction:
    transaction_number: int
    description: str
    amount: float
    date: str
    type: str

@dataclass
class CategorizationPayload:
    context: CategorizationContext
    transactions: List[Transaction]

# --- Categorization Result Structure (matches TypeScript) ---
class Category:
    def __init__(self, category: str, subcategory: str, confidence: float = 0.0, transaction_number: Optional[int] = None):
        self.category = category
        self.subcategory = subcategory
        self.confidence = confidence
        self.transaction_number = transaction_number

    def to_json(self):
        result = {
            "category": self.category,
            "subcategory": self.subcategory,
            "confidence": self.confidence
        }
        if isinstance(self.transaction_number, int):
            result["transaction_number"] = self.transaction_number
        return result

class CategorizationSuccess:
    def __init__(self, items: list):
        self.code = "SUCCESS"
        self.items = items  # List of dicts: {id: str, category: dict or None}

    def to_json(self):
        return {
            "code": self.code,
            "items": self.items
        }

class CategorizationFailure:
    def __init__(self, errors: list):
        self.code = "FAILURE"
        self.errors = errors  # List of dicts: {code: str, description: str}

    def to_json(self):
        return {
            "code": self.code,
            "errors": self.errors
        }

# Union type for result
CategorizationResult = Union[CategorizationSuccess, CategorizationFailure]

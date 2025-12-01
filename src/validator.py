from typing import List, Dict
import pandas as pd
from src.validation_rules import ValidationRule

class DataValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Data Validation Failed with {len(errors)} errors:\n" + "\n".join(errors))

class Validator:
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Run all validation rules on the DataFrame.
        Raises DataValidationError if any rule fails.
        Returns True if all pass.
        """
        errors = []
        for rule in self.rules:
            result = rule.check(df)
            if not result.success:
                errors.append(result.message)
        
        if errors:
            raise DataValidationError(errors)
            
        return True

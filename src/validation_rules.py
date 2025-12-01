from abc import ABC, abstractmethod
import pandas as pd
import re
from typing import Any, Optional

class ValidationResult:
    def __init__(self, success: bool, message: Optional[str] = None):
        self.success = success
        self.message = message

class ValidationRule(ABC):
    def __init__(self, column: str):
        self.column = column

    @abstractmethod
    def check(self, df: pd.DataFrame) -> ValidationResult:
        pass

class NotNullRule(ValidationRule):
    def check(self, df: pd.DataFrame) -> ValidationResult:
        if self.column not in df.columns:
            return ValidationResult(False, f"Column '{self.column}' missing from DataFrame")
        
        null_count = df[self.column].isnull().sum()
        if null_count > 0:
            return ValidationResult(False, f"Column '{self.column}' contains {null_count} null values")
        return ValidationResult(True)

class UniqueRule(ValidationRule):
    def check(self, df: pd.DataFrame) -> ValidationResult:
        if self.column not in df.columns:
            return ValidationResult(False, f"Column '{self.column}' missing from DataFrame")
            
        if not df[self.column].is_unique:
            duplicates = df[self.column].duplicated().sum()
            return ValidationResult(False, f"Column '{self.column}' contains {duplicates} duplicate values")
        return ValidationResult(True)

class TypeRule(ValidationRule):
    def __init__(self, column: str, expected_type: type):
        super().__init__(column)
        self.expected_type = expected_type

    def check(self, df: pd.DataFrame) -> ValidationResult:
        if self.column not in df.columns:
            return ValidationResult(False, f"Column '{self.column}' missing from DataFrame")
            
        # Check if all non-null values match the expected type
        # This is a bit tricky in pandas as columns often have mixed types (object)
        # We'll check a sample or try conversion?
        # Better: check dtypes or apply isinstance
        
        # Simple check: if expected is int, check if pandas dtype is int64 or similar
        # If expected is str, check if object or string
        
        dtype = df[self.column].dtype
        
        if self.expected_type == int:
            if not pd.api.types.is_integer_dtype(dtype):
                 return ValidationResult(False, f"Column '{self.column}' expected int, got {dtype}")
        elif self.expected_type == float:
            if not pd.api.types.is_float_dtype(dtype):
                 return ValidationResult(False, f"Column '{self.column}' expected float, got {dtype}")
        elif self.expected_type == str:
            if not pd.api.types.is_string_dtype(dtype) and not pd.api.types.is_object_dtype(dtype):
                 return ValidationResult(False, f"Column '{self.column}' expected str, got {dtype}")
                 
        return ValidationResult(True)

class RangeRule(ValidationRule):
    def __init__(self, column: str, min_val: Any = None, max_val: Any = None):
        super().__init__(column)
        self.min_val = min_val
        self.max_val = max_val

    def check(self, df: pd.DataFrame) -> ValidationResult:
        if self.column not in df.columns:
            return ValidationResult(False, f"Column '{self.column}' missing from DataFrame")
            
        if self.min_val is not None:
            if (df[self.column] < self.min_val).any():
                count = (df[self.column] < self.min_val).sum()
                return ValidationResult(False, f"Column '{self.column}' has {count} values < {self.min_val}")
                
        if self.max_val is not None:
            if (df[self.column] > self.max_val).any():
                count = (df[self.column] > self.max_val).sum()
                return ValidationResult(False, f"Column '{self.column}' has {count} values > {self.max_val}")
                
        return ValidationResult(True)

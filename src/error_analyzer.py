import re
import traceback
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class ErrorCategory(Enum):
    SCHEMA_DRIFT = "schema_drift"
    TYPE_MISMATCH = "type_mismatch"
    MISSING_DEPENDENCY = "missing_dependency"
    API_ERROR = "api_error"
    DB_CONNECTION = "db_connection"
    SYNTAX_ERROR = "syntax_error"
    FILE_IO = "file_io"
    DATA_QUALITY = "data_quality"
    UNKNOWN = "unknown"

@dataclass
class ErrorDiagnosis:
    category: ErrorCategory
    message: str
    context: Dict[str, Any]
    original_error: str
    suggested_fix_strategy: str

class ErrorAnalyzer:
    """
    Analyzes Python tracebacks and error messages to categorize errors
    and extract relevant context for the AI healer.
    """
    
    def analyze(self, error_log: str) -> ErrorDiagnosis:
        """
        Analyze the error log and return a structured diagnosis.
        """
        category = ErrorCategory.UNKNOWN
        context = {}
        strategy = "Analyze the code and error to find a fix."
        
        # 0. Check for Data Validation Errors
        if "DataValidationError" in error_log or "Data Validation Failed" in error_log:
            category = ErrorCategory.DATA_QUALITY
            strategy = "Data quality issues detected. Consider cleaning the data (e.g., dropping nulls/duplicates) or relaxing validation rules."
            # Extract specific errors
            if "null values" in error_log:
                context['issue'] = "null_values"
            elif "duplicate values" in error_log:
                context['issue'] = "duplicates"

        # 1. Check for Missing Dependencies
        elif "ModuleNotFoundError" in error_log or "ImportError" in error_log:
            category = ErrorCategory.MISSING_DEPENDENCY
            match = re.search(r"No module named '(\w+)'", error_log)
            if match:
                context['missing_module'] = match.group(1)
                strategy = f"Add '{match.group(1)}' to requirements.txt or install it."
            else:
                strategy = "Check imports and installed packages."

        # 2. Check for Schema Drift (KeyError in pandas/dict)
        elif "KeyError" in error_log:
            category = ErrorCategory.SCHEMA_DRIFT
            match = re.search(r"KeyError: '(\w+)'", error_log)
            if match:
                context['missing_column'] = match.group(1)
                strategy = f"The column '{match.group(1)}' is missing from the data. Check for schema changes or renamed columns."
            else:
                strategy = "A required key or column is missing."
                
        # 3. Check for Type Mismatch
        elif "TypeError" in error_log or "ValueError" in error_log:
            # Heuristic: often happens during data processing or schema validation
            if "could not convert" in error_log or "unexpected keyword" in error_log:
                category = ErrorCategory.TYPE_MISMATCH
                strategy = "Check data types and function arguments. Ensure data matches expected format."
            elif "invalid literal" in error_log:
                category = ErrorCategory.TYPE_MISMATCH
                strategy = "Data contains non-numeric values in a numeric column. Use pd.to_numeric(..., errors='coerce') to handle them."
            elif "Schema Mismatch" in error_log: # Custom error from our pipeline
                category = ErrorCategory.SCHEMA_DRIFT
                strategy = "The data schema does not match expectations. Update the code to handle the new schema."
            else:
                category = ErrorCategory.TYPE_MISMATCH
                strategy = "Fix type incompatibility."

        # 4. Check for Syntax Errors
        elif "SyntaxError" in error_log or "IndentationError" in error_log:
            category = ErrorCategory.SYNTAX_ERROR
            strategy = "Fix Python syntax errors."

        # 5. Check for File I/O Errors
        elif "FileNotFoundError" in error_log:
            category = ErrorCategory.FILE_IO
            match = re.search(r"No such file or directory: '(.+)'", error_log)
            if match:
                context['missing_file'] = match.group(1)
                strategy = f"Ensure the file '{match.group(1)}' exists or check the path."
            else:
                strategy = "Check file paths and permissions."

        # 6. Check for API/Network Errors
        elif "ConnectionError" in error_log or "Timeout" in error_log or "401 Client Error" in error_log:
            category = ErrorCategory.API_ERROR
            strategy = "Check network connection, API keys, and service status."

        return ErrorDiagnosis(
            category=category,
            message=error_log.split('\n')[-2] if len(error_log.split('\n')) > 1 else error_log,
            context=context,
            original_error=error_log,
            suggested_fix_strategy=strategy
        )

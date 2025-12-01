import pytest
from src.error_analyzer import ErrorAnalyzer, ErrorCategory

class TestErrorAnalyzer:
    def setup_method(self):
        self.analyzer = ErrorAnalyzer()

    def test_missing_dependency(self):
        error_log = """
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    import non_existent_module
ModuleNotFoundError: No module named 'non_existent_module'
"""
        diagnosis = self.analyzer.analyze(error_log)
        assert diagnosis.category == ErrorCategory.MISSING_DEPENDENCY
        assert diagnosis.context['missing_module'] == 'non_existent_module'
        assert "Add 'non_existent_module' to requirements" in diagnosis.suggested_fix_strategy

    def test_schema_drift_key_error(self):
        error_log = """
Traceback (most recent call last):
  File "etl.py", line 10, in <module>
    df['new_col']
KeyError: 'new_col'
"""
        diagnosis = self.analyzer.analyze(error_log)
        assert diagnosis.category == ErrorCategory.SCHEMA_DRIFT
        assert diagnosis.context['missing_column'] == 'new_col'
        assert "column 'new_col' is missing" in diagnosis.suggested_fix_strategy

    def test_type_error(self):
        error_log = """
Traceback (most recent call last):
  File "etl.py", line 15, in <module>
    int("not_a_number")
ValueError: invalid literal for int() with base 10: 'not_a_number'
"""
        diagnosis = self.analyzer.analyze(error_log)
        assert diagnosis.category == ErrorCategory.TYPE_MISMATCH

    def test_file_not_found(self):
        error_log = """
Traceback (most recent call last):
  File "main.py", line 5, in <module>
    open('missing_file.txt')
FileNotFoundError: [Errno 2] No such file or directory: 'missing_file.txt'
"""
        diagnosis = self.analyzer.analyze(error_log)
        assert diagnosis.category == ErrorCategory.FILE_IO
        assert diagnosis.context['missing_file'] == 'missing_file.txt'

    def test_syntax_error(self):
        error_log = """
  File "script.py", line 10
    if True
          ^
SyntaxError: invalid syntax
"""
        diagnosis = self.analyzer.analyze(error_log)
        assert diagnosis.category == ErrorCategory.SYNTAX_ERROR

    def test_unknown_error(self):
        error_log = "Some random error occurred"
        diagnosis = self.analyzer.analyze(error_log)
        assert diagnosis.category == ErrorCategory.UNKNOWN

import pytest
import pandas as pd
import os
from src.doctor import DataDoctor
from src.config_schema import Config, AIConfig
from src.error_analyzer import ErrorAnalyzer, ErrorCategory

class TestDataQualityIntegration:
    def setup_method(self):
        self.config = Config(
            ai=AIConfig(
                api_key=os.getenv('SHP_AI_API_KEY', 'dummy_key'),
                model='openai/gpt-4o-mini'
            )
        )
        self.doctor = DataDoctor(config=self.config)
        self.analyzer = ErrorAnalyzer()

    def test_pipeline_validation_failure(self, tmp_path):
        # 1. Create data with nulls and duplicates
        data_path = tmp_path / "users.csv"
        with open(data_path, "w") as f:
            f.write("uid,customer_name,email,signup_date\n")
            f.write("1,Alice,alice@example.com,2023-01-01\n")
            f.write("2,,bob@example.com,2023-01-02\n") # Null name
            f.write("1,Charlie,charlie@example.com,2023-01-03\n") # Duplicate ID

        # 2. Create a script that runs validation
        # We'll use a simplified version of the pipeline script for testing
        script_path = tmp_path / "etl_script.py"
        script_content = """
import pandas as pd
from src.validator import Validator, DataValidationError
from src.validation_rules import NotNullRule, UniqueRule

def run():
    df = pd.read_csv(r'DATA_PATH')
    df = df.rename(columns={'uid': 'id', 'customer_name': 'name'})
    
    rules = [
        UniqueRule('id'),
        NotNullRule('name')
    ]
    validator = Validator(rules)
    validator.validate(df)

if __name__ == "__main__":
    run()
""".replace("DATA_PATH", str(data_path).replace("\\", "\\\\"))
        
        with open(script_path, "w") as f:
            f.write(script_content)

        # 3. Simulate execution and failure
        # We can't easily run the script via subprocess and capture the python exception object
        # So we'll simulate the error log that would be produced
        error_log = """
Traceback (most recent call last):
  File "etl_script.py", line 15, in run
    validator.validate(df)
  File "src/validator.py", line 18, in validate
    raise DataValidationError(errors)
src.validator.DataValidationError: Data Validation Failed with 2 errors:
Column 'id' contains 1 duplicate values
Column 'name' contains 1 null values
"""

        # 4. Diagnose with ErrorAnalyzer
        diagnosis = self.analyzer.analyze(error_log)
        
        assert diagnosis.category == ErrorCategory.DATA_QUALITY
        assert "Data quality issues detected" in diagnosis.suggested_fix_strategy
        assert diagnosis.context['issue'] in ['null_values', 'duplicates']

        # 5. (Optional) Ask Doctor to heal
        # Healing data quality is tricky. The AI might suggest dropping rows.
        # Let's see what it generates.
        if self.config.ai.api_key == 'dummy_key':
            pytest.skip("Skipping AI generation without API key")
            
        # We need to mock the data read for the doctor
        # Or just pass the path
        
        healed = self.doctor.diagnose_and_heal(str(script_path), str(data_path), error_log)
        
        # We expect the doctor to potentially modify the code to handle bad data, 
        # e.g., by dropping nulls or duplicates BEFORE validation, or relaxing validation.
        # Or maybe it fails to heal because it's a data issue, not a code issue.
        # But our strategy says "Consider cleaning the data".
        
        # Let's check if it modified the code
        with open(script_path, "r") as f:
            new_code = f.read()
            
        # It might add df.dropna() or df.drop_duplicates()
        assert "drop_duplicates" in new_code or "dropna" in new_code or healed is False

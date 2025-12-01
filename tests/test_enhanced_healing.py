import pytest
import pandas as pd
import os
from src.doctor import DataDoctor
from src.config_manager import ConfigManager
from src.config_schema import Config, AIConfig

class TestEnhancedHealing:
    def setup_method(self):
        # Create a dummy config
        self.config = Config(
            ai=AIConfig(
                api_key=os.getenv('SHP_AI_API_KEY', 'dummy_key'),
                model='openai/gpt-4o-mini'
            )
        )
        self.doctor = DataDoctor(config=self.config)

    def test_type_mismatch_healing(self, tmp_path):
        # 1. Create a CSV with a string in an integer column
        data_path = tmp_path / "data.csv"
        with open(data_path, "w") as f:
            f.write("id,value\n1,100\n2,not_a_number\n3,300")
            
        # 2. Create a script that expects integers and fails
        script_path = tmp_path / "etl_script.py"
        script_content = """
import pandas as pd

def run():
    df = pd.read_csv(r'DATA_PATH')
    # This will fail if value is not numeric
    total = df['value'].astype(int).sum()
    print(f"Total: {total}")

if __name__ == "__main__":
    run()
""".replace("DATA_PATH", str(data_path).replace("\\", "\\\\"))
        
        with open(script_path, "w") as f:
            f.write(script_content)
            
        # 3. Simulate the error log
        error_log = """
Traceback (most recent call last):
  File "etl_script.py", line 6, in run
    total = df['value'].astype(int).sum()
ValueError: invalid literal for int() with base 10: 'not_a_number'
"""

        # 4. Run the doctor
        # Note: We need a real API key for this to actually generate code.
        # If no key is present, we might mock the LLM or skip.
        if self.config.ai.api_key == 'dummy_key':
            pytest.skip("Skipping integration test without API key")
            
        healed = self.doctor.diagnose_and_heal(str(script_path), str(data_path), error_log)
        
        assert healed is True
        
        # 5. Verify the fix
        with open(script_path, "r") as f:
            new_code = f.read()
            
        # The fix should handle non-numeric values, e.g., using pd.to_numeric with errors='coerce'
        assert "pd.to_numeric" in new_code or "errors='coerce'" in new_code or "try" in new_code

    def test_missing_dependency_healing(self, tmp_path):
        # 1. Create a script with missing dependency
        script_path = tmp_path / "missing_dep.py"
        with open(script_path, "w") as f:
            f.write("import non_existent_package\n")
            
        # 2. Error log
        error_log = "ModuleNotFoundError: No module named 'non_existent_package'"
        
        # 3. Run doctor
        if self.config.ai.api_key == 'dummy_key':
            pytest.skip("Skipping integration test without API key")
            
        # We need a dummy data path even if not used
        data_path = tmp_path / "dummy.csv"
        with open(data_path, "w") as f:
            f.write("col1\n1")

        healed = self.doctor.diagnose_and_heal(str(script_path), str(data_path), error_log)
        
        # The fix might be to try installing it (which we can't do in code easily without running subprocess)
        # or commenting it out, or handling the import error.
        # Since we asked for "Python code only", the AI might wrap it in try-except or suggest installation in comments.
        # Let's see what it does.
        assert healed is True

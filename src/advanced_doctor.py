import pandas as pd
import sys
import os
from openai import OpenAI
from src.rollback_manager import RollbackManager
from src.error_analyzer import ErrorAnalyzer, ErrorCategory

class AdvancedLLM:
    def __init__(self, config):
        """Initialize LLM with configuration."""
        self.config = config
        self.client = OpenAI(
            api_key=config.ai.api_key,
            base_url=config.ai.base_url
        )
    
    def generate_fix(self, error_log, code_content, data_head, attempt=1, previous_fix=None, previous_error=None, diagnosis=None):
        '''Generate fix with feedback from previous attempts.'''
        print(f'🤖 LLM: Analyzing error (Attempt {attempt}/{self.config.healing.max_attempts})...')
        
        # Enhanced prompt with diagnosis context
        context_str = ""
        if diagnosis:
            print(f'🔍 Diagnosis: {diagnosis.category.value} - {diagnosis.suggested_fix_strategy}')
            context_str = f"""
DIAGNOSIS:
Category: {diagnosis.category.value}
Context: {diagnosis.context}
Strategy: {diagnosis.suggested_fix_strategy}
"""

        if attempt == 1:
            prompt = f'''You are a data engineering expert. A Python ETL pipeline has failed.

ERROR LOG:
{error_log}

{context_str}

CURRENT CODE:
{code_content}

DATA COLUMNS (from CSV):
{data_head}

TASK: Fix the code to handle the error. Return ONLY the corrected Python code, nothing else. No explanations, no markdown formatting, just the raw Python code.'''
        else:
            prompt = f'''You are a data engineering expert. Your previous fix did not work.

ORIGINAL ERROR:
{error_log}

YOUR PREVIOUS FIX (Attempt {attempt-1}):
{previous_fix}

NEW ERROR AFTER YOUR FIX:
{previous_error}

{context_str}

DATA COLUMNS (from CSV):
{data_head}

TASK: The previous fix failed. Analyze what went wrong and provide a BETTER fix. Return ONLY the corrected Python code, nothing else.'''

        try:
            response = self.client.chat.completions.create(
                model=self.config.ai.model,
                messages=[
                    {"role": "system", "content": "You are a code fixing assistant. Return only valid Python code with no explanations or markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.ai.temperature,
                max_tokens=self.config.ai.max_tokens,
                timeout=self.config.ai.timeout
            )
            
            fixed_code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if fixed_code.startswith('```python'):
                fixed_code = fixed_code.split('```python')[1].split('```')[0].strip()
            elif fixed_code.startswith('```'):
                fixed_code = fixed_code.split('```')[1].split('```')[0].strip()
            
            print(f'✓ LLM: Fix generated for attempt {attempt}.')
            return fixed_code
            
        except Exception as e:
            print(f'✗ LLM: Error calling AI: {e}')
            return code_content

class AdvancedDataDoctor:
    def __init__(self, config=None, api_key=None, max_attempts=None):
        """
        Initialize AdvancedDataDoctor with configuration.
        
        Args:
            config: Config object (preferred)
            api_key: API key string (deprecated, for backward compatibility)
            max_attempts: Max healing attempts (deprecated, use config)
        """
        if config:
            self.config = config
            self.llm = AdvancedLLM(config)
            self.max_attempts = config.healing.max_attempts
        elif api_key:
            # Backward compatibility: create minimal config from API key
            from src.config_schema import Config, AIConfig, HealingConfig
            self.config = Config(
                ai=AIConfig(api_key=api_key),
                healing=HealingConfig(max_attempts=max_attempts or 3)
            )
            self.llm = AdvancedLLM(self.config)
            self.max_attempts = max_attempts or 3
        else:
            raise ValueError('Either config or api_key is required')
        self.rollback_manager = RollbackManager()
        self.analyzer = ErrorAnalyzer()

    def diagnose_and_heal(self, script_path, data_path, error_log):
        '''Multi-attempt healing with feedback loop and rollback.'''
        print(f' Advanced Doctor is examining {script_path}...')
        
        # 1. Analyze the error
        diagnosis = self.analyzer.analyze(error_log)

        # Create backup before any changes
        backup_path = self.rollback_manager.create_backup(script_path)
        
        # Read the broken code
        with open(script_path, 'r') as f:
            original_code = f.read()
            
        # Read the data head
        try:
            df = pd.read_csv(data_path, nrows=2)
            data_head = str(df.columns.tolist())
            # Also get dtypes for type mismatch context
            data_types = str(df.dtypes.to_dict())
            data_head += f"\nData Types: {data_types}"
        except Exception as e:
            data_head = f'Could not read data: {e}'

        current_code = original_code
        previous_fix = None
        previous_error = None
        
        for attempt in range(1, self.max_attempts + 1):
            print(f'\n Healing Attempt {attempt}/{self.max_attempts}')
            
            # Generate fix
            fixed_code = self.llm.generate_fix(
                error_log, 
                current_code, # Pass current_code for the LLM to consider
                data_head, 
                attempt, 
                previous_fix, 
                previous_error,
                diagnosis
            )
            
            if fixed_code == current_code:
                print(' Doctor could not generate a new fix.')
                break # Exit loop if LLM can't generate a different fix
            
            # Apply the fix
            print(' Applying fix...')
            with open(script_path, 'w') as f:
                f.write(fixed_code)
            
            # Test the fix
            print(' Testing the fix...')
            test_result, test_error = self._test_fix(script_path)
            
            if test_result:
                print(f' Fix successful on attempt {attempt}!')
                return True
            else:
                print(f' Fix failed. Error: {test_error}')
                previous_fix = fixed_code
                previous_error = test_error
                current_code = fixed_code # Update current_code for the next attempt
        
        # All attempts failed, rollback
        print(f'\n All {self.max_attempts} attempts failed. Rolling back...')
        self.rollback_manager.rollback(script_path, backup_path)
        return False

    def _test_fix(self, script_path):
        '''Test if the fix works by running the script.'''
        import subprocess
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr

if __name__ == '__main__':
    pass

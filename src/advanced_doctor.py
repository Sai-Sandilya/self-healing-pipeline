import pandas as pd
import sys
import os
from openai import OpenAI
from src.rollback_manager import RollbackManager

class AdvancedLLM:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url='https://openrouter.ai/api/v1'
        )
    
    def generate_fix(self, error_log, code_content, data_head, attempt=1, previous_fix=None, previous_error=None):
        '''Generate fix with feedback from previous attempts.'''
        print(f' LLM: Analyzing error (Attempt {attempt}/3)...')
        
        if attempt == 1:
            prompt = f'''You are a data engineering expert. A Python ETL pipeline has failed.

ERROR LOG:
{error_log}

CURRENT CODE:
{code_content}

DATA COLUMNS (from CSV):
{data_head}

TASK: Fix the code to handle the new schema. Return ONLY the corrected Python code, nothing else. No explanations, no markdown formatting, just the raw Python code.'''
        else:
            prompt = f'''You are a data engineering expert. Your previous fix did not work.

ORIGINAL ERROR:
{error_log}

YOUR PREVIOUS FIX (Attempt {attempt-1}):
{previous_fix}

NEW ERROR AFTER YOUR FIX:
{previous_error}

DATA COLUMNS (from CSV):
{data_head}

TASK: The previous fix failed. Analyze what went wrong and provide a BETTER fix. Return ONLY the corrected Python code, nothing else.'''

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a code fixing assistant. Return only valid Python code with no explanations or markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            fixed_code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if fixed_code.startswith('`python'):
                fixed_code = fixed_code.split('`python')[1].split('`')[0].strip()
            elif fixed_code.startswith('`'):
                fixed_code = fixed_code.split('`')[1].split('`')[0].strip()
            
            print(f' LLM: Fix generated for attempt {attempt}.')
            return fixed_code
            
        except Exception as e:
            print(f' LLM: Error calling AI: {e}')
            return code_content

class AdvancedDataDoctor:
    def __init__(self, api_key=None, max_attempts=3):
        if api_key:
            self.llm = AdvancedLLM(api_key)
        else:
            raise ValueError('API key is required')
        self.max_attempts = max_attempts
        self.rollback_manager = RollbackManager()

    def diagnose_and_heal(self, script_path, data_path, error_log):
        '''Multi-attempt healing with feedback loop and rollback.'''
        print(f' Advanced Doctor is examining {script_path}...')
        
        # Create backup before any changes
        backup_path = self.rollback_manager.create_backup(script_path)
        
        # Read the broken code
        with open(script_path, 'r') as f:
            original_code = f.read()
            
        # Read the data head
        try:
            df = pd.read_csv(data_path, nrows=2)
            data_head = str(df.columns.tolist())
        except Exception as e:
            data_head = f'Could not read data: {e}'

        previous_fix = None
        previous_error = None
        
        for attempt in range(1, self.max_attempts + 1):
            print(f'\n Healing Attempt {attempt}/{self.max_attempts}')
            
            # Generate fix
            fixed_code = self.llm.generate_fix(
                error_log, 
                original_code if attempt == 1 else previous_fix, 
                data_head, 
                attempt, 
                previous_fix, 
                previous_error
            )
            
            if fixed_code == original_code:
                print(' LLM could not generate a fix.')
                continue
            
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

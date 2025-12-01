import pandas as pd
import sys
import os
from openai import OpenAI

class RealLLM:
    def __init__(self, api_key):
        # The API key format 'sk-or-v1-' indicates OpenRouter, not OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url='https://openrouter.ai/api/v1'
        )
    
    def generate_fix(self, error_log, code_content, data_head):
        print(' LLM: Analyzing error with AI (via OpenRouter)...')
        
        prompt = f'''You are a data engineering expert. A Python ETL pipeline has failed.

ERROR LOG:
{error_log}

CURRENT CODE:
{code_content}

DATA COLUMNS (from CSV):
{data_head}

TASK: Fix the code to handle the new schema. Return ONLY the corrected Python code, nothing else. No explanations, no markdown formatting, just the raw Python code.'''

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",  # OpenRouter format
                messages=[
                    {"role": "system", "content": "You are a code fixing assistant. Return only valid Python code with no explanations or markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0  # Deterministic responses
            )
            
            fixed_code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if fixed_code.startswith('`python'):
                fixed_code = fixed_code.split('`python')[1].split('`')[0].strip()
            elif fixed_code.startswith('`'):
                fixed_code = fixed_code.split('`')[1].split('`')[0].strip()
            
            print(' LLM: Fix generated successfully.')
            return fixed_code
            
        except Exception as e:
            print(f' LLM: Error calling AI: {e}')
            return code_content

class DataDoctor:
    def __init__(self, api_key=None):
        if api_key:
            self.llm = RealLLM(api_key)
        else:
            raise ValueError('API key is required for real LLM integration')

    def diagnose_and_heal(self, script_path, data_path, error_log):
        print(f' Doctor is examining {script_path}...')
        
        # 1. Read the broken code
        with open(script_path, 'r') as f:
            code_content = f.read()
            
        # 2. Read the data head to understand the new schema
        try:
            df = pd.read_csv(data_path, nrows=2)
            data_head = str(df.columns.tolist())
        except Exception as e:
            data_head = f'Could not read data: {e}'

        # 3. Ask LLM for a fix
        fixed_code = self.llm.generate_fix(error_log, code_content, data_head)
        
        # 4. Apply the fix
        if fixed_code != code_content:
            print(' Doctor is applying the fix...')
            with open(script_path, 'w') as f:
                f.write(fixed_code)
            print(' Fix applied successfully!')
            return True
        else:
            print(' Doctor could not find a fix.')
            return False

if __name__ == '__main__':
    # For testing purposes
    pass

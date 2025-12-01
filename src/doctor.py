import pandas as pd
import sys
import os
from openai import OpenAI
from src.error_analyzer import ErrorAnalyzer, ErrorCategory

class RealLLM:
    def __init__(self, config):
        """Initialize LLM with configuration."""
        self.config = config
        self.client = OpenAI(
            api_key=config.ai.api_key,
            base_url=config.ai.base_url
        )
    
    def generate_fix(self, error_log, code_content, data_head, diagnosis=None):
        print(f'🤖 LLM: Analyzing error with {self.config.ai.model}...')
        
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

        prompt = f'''You are a data engineering expert. A Python ETL pipeline has failed.

ERROR LOG:
{error_log}

{context_str}

CURRENT CODE:
{code_content}

DATA COLUMNS (from CSV):
{data_head}

TASK: Fix the code to handle the error. Return ONLY the corrected Python code, nothing else. No explanations, no markdown formatting, just the raw Python code.'''

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
            
            print('✓ LLM: Fix generated successfully.')
            return fixed_code
            
        except Exception as e:
            print(f'✗ LLM: Error calling AI: {e}')
            with open('debug_doctor.log', 'a') as log:
                log.write(f'ERROR: LLM call failed: {e}\n')
            return code_content

class DataDoctor:
    def __init__(self, config=None, api_key=None):
        """
        Initialize DataDoctor with configuration.
        
        Args:
            config: Config object (preferred)
            api_key: API key string (deprecated, for backward compatibility)
        """
        if config:
            self.config = config
            self.llm = RealLLM(config)
        elif api_key:
            # Backward compatibility: create minimal config from API key
            from src.config_schema import Config, AIConfig
            self.config = Config(ai=AIConfig(api_key=api_key))
            self.llm = RealLLM(self.config)
        else:
            raise ValueError('Either config or api_key is required')
        
        self.analyzer = ErrorAnalyzer()

    def diagnose_and_heal(self, script_path, data_path, error_log):
        print(f' Doctor is examining {script_path}...')
        
        # 1. Analyze the error
        diagnosis = self.analyzer.analyze(error_log)
        
        # 2. Read the broken code
        with open(script_path, 'r') as f:
            code_content = f.read()
            
        # 3. Read the data head to understand the new schema
        try:
            df = pd.read_csv(data_path, nrows=2)
            data_head = str(df.columns.tolist())
            # Also get dtypes for type mismatch context
            data_types = str(df.dtypes.to_dict())
            data_head += f"\nData Types: {data_types}"
        except Exception as e:
            data_head = f'Could not read data: {e}'

        # 4. Ask LLM for a fix with diagnosis
        fixed_code = self.llm.generate_fix(error_log, code_content, data_head, diagnosis)
        
        # 5. Apply the fix
        if fixed_code != code_content:
            print(' Doctor is applying the fix...')
            with open(script_path, 'w') as f:
                f.write(fixed_code)
            print(' Fix applied successfully!')
            return True
        else:
            print(' Doctor could not find a fix.')
            with open('debug_doctor.log', 'w') as log:
                log.write(f'DEBUG: Code length original: {len(code_content)}, fixed: {len(fixed_code)}\n')
                log.write(f'DEBUG: First 50 chars original: {code_content[:50]}\n')
                log.write(f'DEBUG: First 50 chars fixed: {fixed_code[:50]}\n')
                log.write(f'DEBUG: Full fixed code:\n{fixed_code}\n')
            return False

if __name__ == '__main__':
    # For testing purposes
    pass

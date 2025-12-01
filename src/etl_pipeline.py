import pandas as pd
import sys
import os

from src.validator import Validator, DataValidationError
from src.validation_rules import NotNullRule, UniqueRule, TypeRule

def run_pipeline():
    print('Starting ETL pipeline...')
    try:
        # Ensure directories exist
        os.makedirs(r'E:\self_healing_pipeline\data\processed', exist_ok=True)
        
        df = pd.read_csv(r'E:\self_healing_pipeline\data\raw\users.csv')
        
        # Update renaming to match new schema
        df = df.rename(columns={
            'uid': 'id',
            'customer_name': 'name',
            'email': 'email_address',
            'signup_date': 'created_at'
        })
        
        # Check if columns exist
        required_cols = ['id', 'name', 'email_address', 'created_at']
        if not all(col in df.columns for col in required_cols):
             missing = [c for c in required_cols if c not in df.columns]
             raise ValueError(f'Schema Mismatch! Missing columns after rename: {missing}. Did input columns change?')

        # --- Data Validation ---
        print('Running data validation...')
        rules = [
            UniqueRule('id'),
            NotNullRule('name'),
            NotNullRule('email_address')
        ]
        validator = Validator(rules)
        validator.validate(df)
        print('Data validation passed.')
        # -----------------------

        # Some transformation
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        output_path = r'E:\self_healing_pipeline\data\processed\users_processed.csv'
        df.to_csv(output_path, index=False)
        print(f'Pipeline finished successfully. Data saved to {output_path}')
        return True
    except DataValidationError as e:
        print(f'Data Validation Failed:\n{e}')
        raise e
    except Exception as e:
        print(f'Pipeline Failed: {e}')
        raise e

if __name__ == '__main__':
    run_pipeline()
import pandas as pd
import random

def unleash_chaos():
    print(' Chaos Monkey is loose! modifying schema...')
    file_path = r'E:\self_healing_pipeline\data\raw\users.csv'
    df = pd.read_csv(file_path)
    
    # Simulate a breaking change: 'user_id' -> 'uid'
    if 'user_id' in df.columns:
        df = df.rename(columns={'user_id': 'uid'})
        print('Changed column: user_id -> uid')
    
    # Simulate another change: 'full_name' -> 'customer_name'
    if 'full_name' in df.columns:
        df = df.rename(columns={'full_name': 'customer_name'})
        print('Changed column: full_name -> customer_name')
        
    df.to_csv(file_path, index=False)
    print('Chaos unleashed. Schema corrupted.')

if __name__ == '__main__':
    unleash_chaos()

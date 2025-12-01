import unittest
import pandas as pd
import os
import sys

# Add src to path so we can import the pipeline logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from etl_pipeline import run_pipeline

class TestETLEdgeCases(unittest.TestCase):
    
    def setUp(self):
        self.test_data_dir = r'E:\self_healing_pipeline\data\raw'
        self.test_file = os.path.join(self.test_data_dir, 'users.csv')
        os.makedirs(self.test_data_dir, exist_ok=True)

    def tearDown(self):
        # Clean up after tests
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def create_dummy_csv(self, content):
        with open(self.test_file, 'w') as f:
            f.write(content)

    def test_empty_csv(self):
        """Test how the pipeline handles an empty file."""
        print("\n[Test] Empty CSV")
        self.create_dummy_csv("") 
        # Pandas read_csv on empty file raises EmptyDataError
        with self.assertRaises(pd.errors.EmptyDataError):
            run_pipeline()

    def test_extra_columns(self):
        """Test if extra columns cause failure (they shouldn't if we just rename known ones)."""
        print("\n[Test] Extra Columns")
        # 'age' is an extra column
        content = "user_id,full_name,email,signup_date,age\n1,Alice,alice@example.com,2023-01-01,30"
        self.create_dummy_csv(content)
        
        try:
            run_pipeline()
        except Exception as e:
            self.fail(f"Pipeline failed with extra columns: {e}")

    def test_missing_columns(self):
        """Test if missing columns cause immediate failure."""
        print("\n[Test] Missing Columns")
        # 'email' is missing
        content = "user_id,full_name,signup_date\n1,Alice,2023-01-01"
        self.create_dummy_csv(content)
        
        with self.assertRaises(ValueError):
            run_pipeline()

    def test_malformed_date(self):
        """Test if invalid dates cause failure."""
        print("\n[Test] Malformed Date")
        content = "user_id,full_name,email,signup_date\n1,Alice,alice@example.com,NOT_A_DATE"
        self.create_dummy_csv(content)
        
        with self.assertRaises(Exception):
            run_pipeline()

if __name__ == '__main__':
    unittest.main()

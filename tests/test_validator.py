import pytest
import pandas as pd
import numpy as np
from src.validator import Validator, DataValidationError
from src.validation_rules import NotNullRule, UniqueRule, TypeRule, RangeRule

class TestValidator:
    def test_not_null_rule(self):
        df = pd.DataFrame({'a': [1, 2, None]})
        rule = NotNullRule('a')
        result = rule.check(df)
        assert result.success is False
        assert "contains 1 null values" in result.message

        df_clean = pd.DataFrame({'a': [1, 2, 3]})
        assert rule.check(df_clean).success is True

    def test_unique_rule(self):
        df = pd.DataFrame({'id': [1, 2, 2]})
        rule = UniqueRule('id')
        result = rule.check(df)
        assert result.success is False
        assert "contains 1 duplicate values" in result.message

    def test_range_rule(self):
        df = pd.DataFrame({'age': [20, 15, 60]})
        rule = RangeRule('age', min_val=18)
        result = rule.check(df)
        assert result.success is False
        assert "values < 18" in result.message

    def test_validator_aggregation(self):
        df = pd.DataFrame({
            'id': [1, 2, 2],      # Duplicate
            'age': [20, None, 15] # Null and < 18
        })
        
        rules = [
            UniqueRule('id'),
            NotNullRule('age'),
            RangeRule('age', min_val=18)
        ]
        
        validator = Validator(rules)
        
        with pytest.raises(DataValidationError) as excinfo:
            validator.validate(df)
        
        assert "contains 1 duplicate values" in str(excinfo.value)
        assert "contains 1 null values" in str(excinfo.value)
        assert "values < 18" in str(excinfo.value)

    def test_validator_success(self):
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'age': [20, 25, 30]
        })
        rules = [UniqueRule('id'), RangeRule('age', min_val=18)]
        validator = Validator(rules)
        assert validator.validate(df) is True

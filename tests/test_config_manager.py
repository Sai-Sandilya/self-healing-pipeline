"""
Comprehensive unit tests for ConfigManager.
Tests cover YAML loading, environment overrides, validation, and edge cases.
"""
import pytest
import os
import yaml
import tempfile
from pathlib import Path
from src.config_manager import ConfigManager
from src.config_schema import Config
from pydantic import ValidationError


class TestConfigManager:
    """Test suite for ConfigManager functionality."""
    
    def setup_method(self):
        """Reset ConfigManager singleton before each test."""
        ConfigManager.reset()
    
    def teardown_method(self):
        """Clean up after each test."""
        ConfigManager.reset()
        # Clean up environment variables
        for key in list(os.environ.keys()):
            if key.startswith('SHP_'):
                del os.environ[key]
    
    def test_load_basic_config(self, tmp_path):
        """Test loading a basic valid configuration."""
        config_data = {
            'environment': {'env': 'development', 'debug': True, 'log_level': 'INFO'},
            'paths': {'data_dir': 'data/raw', 'logs_dir': 'logs'},
            'ai': {
                'api_key': 'test-key-123',
                'base_url': 'https://api.test.com',
                'model': 'test-model',
                'temperature': 0.0
            },
            'healing': {'max_attempts': 3},
            'monitoring': {'enable_monitoring': True},
            'github': {'enable_github': False},
            'security': {'enable_audit_log': True},
            'performance': {'enable_caching': True}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        assert config.ai.api_key == 'test-key-123'
        assert config.ai.model == 'test-model'
        assert config.healing.max_attempts == 3
        assert config.environment.env == 'development'
    
    def test_load_config_with_env_override(self, tmp_path):
        """Test that environment variables override config file values."""
        config_data = {
            'ai': {'api_key': 'file-key', 'temperature': 0.5},
            'healing': {'max_attempts': 3}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Set environment overrides
        os.environ['SHP_AI__API_KEY'] = 'env-key-override'
        os.environ['SHP_HEALING__MAX_ATTEMPTS'] = '5'
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        assert config.ai.api_key == 'env-key-override'
        assert config.healing.max_attempts == 5
    
    def test_environment_specific_config_merge(self, tmp_path):
        """Test merging environment-specific configuration."""
        base_config = {
            'ai': {'api_key': 'base-key', 'temperature': 0.0, 'model': 'base-model'},
            'healing': {'max_attempts': 3}
        }
        
        dev_config = {
            'ai': {'temperature': 0.5},  # Override only temperature
            'healing': {'max_attempts': 2}
        }
        
        base_file = tmp_path / "config.yaml"
        dev_file = tmp_path / "config.development.yaml"
        
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        with open(dev_file, 'w') as f:
            yaml.dump(dev_config, f)
        
        manager = ConfigManager()
        config = manager.load_config(str(base_file), env='development', load_env_file=False)
        
        assert config.ai.api_key == 'base-key'  # From base
        assert config.ai.model == 'base-model'  # From base
        assert config.ai.temperature == 0.5  # Overridden by dev
        assert config.healing.max_attempts == 2  # Overridden by dev
    
    def test_missing_config_file(self):
        """Test error handling when config file doesn't exist."""
        manager = ConfigManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_config('/nonexistent/config.yaml', load_env_file=False)
    
    def test_invalid_yaml(self, tmp_path):
        """Test error handling for malformed YAML."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content:\n  - broken")
        
        manager = ConfigManager()
        
        with pytest.raises(ValueError, match="Invalid YAML"):
            manager.load_config(str(config_file), load_env_file=False)
    
    def test_empty_config_file(self, tmp_path):
        """Test handling of empty config file."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()  # Create empty file
        
        manager = ConfigManager()
        
        # Should fail validation due to missing required fields
        with pytest.raises(ValueError):
            manager.load_config(str(config_file), load_env_file=False)
    
    def test_missing_required_field(self, tmp_path):
        """Test validation error when required field is missing."""
        config_data = {
            'environment': {'env': 'development'},
            'paths': {'data_dir': 'data'},
            # Missing 'ai' section with required api_key
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        
        with pytest.raises(ValueError):
            manager.load_config(str(config_file), load_env_file=False)
    
    def test_invalid_data_type(self, tmp_path):
        """Test validation error for invalid data types."""
        config_data = {
            'ai': {'api_key': 'test-key', 'temperature': 'not-a-number'},  # Should be float
            'healing': {'max_attempts': 'three'}  # Should be int
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        
        with pytest.raises(ValueError):
            manager.load_config(str(config_file), load_env_file=False)
    
    def test_env_value_conversion(self, tmp_path):
        """Test automatic type conversion of environment variables."""
        config_data = {
            'ai': {'api_key': 'test-key', 'temperature': 0.0},
            'healing': {'max_attempts': 1, 'enable_rollback': False}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Set various types via environment
        os.environ['SHP_HEALING__MAX_ATTEMPTS'] = '10'  # String -> int
        os.environ['SHP_HEALING__ENABLE_ROLLBACK'] = 'true'  # String -> bool
        os.environ['SHP_AI__TEMPERATURE'] = '0.7'  # String -> float
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        assert config.healing.max_attempts == 10
        assert isinstance(config.healing.max_attempts, int)
        assert config.healing.enable_rollback is True
        assert isinstance(config.healing.enable_rollback, bool)
        assert config.ai.temperature == 0.7
        assert isinstance(config.ai.temperature, float)
    
    def test_boolean_env_values(self, tmp_path):
        """Test various boolean representations in environment variables."""
        config_data = {
            'ai': {'api_key': 'test-key'},
            'healing': {'enable_rollback': False, 'enable_backup': False}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test various true values
        os.environ['SHP_HEALING__ENABLE_ROLLBACK'] = 'yes'
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        assert config.healing.enable_rollback is True
        
        ConfigManager.reset()
        os.environ['SHP_HEALING__ENABLE_ROLLBACK'] = '1'
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        assert config.healing.enable_rollback is True
        
        # Test various false values
        ConfigManager.reset()
        os.environ['SHP_HEALING__ENABLE_BACKUP'] = 'no'
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        assert config.healing.enable_backup is False
    
    def test_singleton_pattern(self, tmp_path):
        """Test that ConfigManager follows singleton pattern."""
        config_data = {'ai': {'api_key': 'test-key'}}
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        assert manager1 is manager2
    
    def test_get_config_before_load(self):
        """Test error when trying to get config before loading."""
        manager = ConfigManager()
        
        with pytest.raises(RuntimeError, match="Configuration not loaded"):
            manager.get_config()
    
    def test_reload_config(self, tmp_path):
        """Test reloading configuration."""
        config_data = {'ai': {'api_key': 'original-key'}}
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        config1 = manager.load_config(str(config_file), load_env_file=False)
        assert config1.ai.api_key == 'original-key'
        
        # Modify config file
        config_data['ai']['api_key'] = 'new-key'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config2 = manager.reload_config(str(config_file))
        assert config2.ai.api_key == 'new-key'
    
    def test_deep_merge(self, tmp_path):
        """Test deep merging of nested configurations."""
        base_config = {
            'ai': {
                'api_key': 'base-key',
                'model': 'base-model',
                'temperature': 0.0,
                'max_tokens': 1000
            }
        }
        
        override_config = {
            'ai': {
                'temperature': 0.5,
                'timeout': 30
            }
        }
        
        base_file = tmp_path / "config.yaml"
        override_file = tmp_path / "config.development.yaml"
        
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        with open(override_file, 'w') as f:
            yaml.dump(override_config, f)
        
        manager = ConfigManager()
        config = manager.load_config(str(base_file), env='development', load_env_file=False)
        
        # Check that base values are preserved
        assert config.ai.api_key == 'base-key'
        assert config.ai.model == 'base-model'
        assert config.ai.max_tokens == 1000
        
        # Check that overrides are applied
        assert config.ai.temperature == 0.5
        assert config.ai.timeout == 30
    
    def test_unicode_in_paths(self, tmp_path):
        """Test handling of Unicode characters in paths."""
        config_data = {
            'ai': {'api_key': 'test-key'},
            'paths': {'data_dir': 'data/测试/raw'}  # Chinese characters
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True)
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        assert '测试' in str(config.paths.data_dir)
    
    def test_special_characters_in_values(self, tmp_path):
        """Test handling of special characters in configuration values."""
        config_data = {
            'ai': {
                'api_key': 'key-with-special-chars-!@#$%^&*()',
                'base_url': 'https://api.test.com/v1?param=value&other=123'
            }
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        assert config.ai.api_key == 'key-with-special-chars-!@#$%^&*()'
        assert '?' in config.ai.base_url
        assert '&' in config.ai.base_url
    
    def test_extra_fields_ignored(self, tmp_path):
        """Test that extra unknown fields don't cause errors."""
        config_data = {
            'ai': {'api_key': 'test-key', 'unknown_field': 'should-be-ignored'},
            'unknown_section': {'foo': 'bar'}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        # Should load successfully, ignoring extra fields
        config = manager.load_config(str(config_file), load_env_file=False)
        assert config.ai.api_key == 'test-key'
    
    def test_env_variable_expansion(self, tmp_path):
        """Test expansion of environment variables in config values."""
        os.environ['TEST_API_KEY'] = 'expanded-key-123'
        
        config_data = {
            'ai': {'api_key': '${TEST_API_KEY}'}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        # Note: expandvars is applied to paths, not all strings
        # This test documents current behavior
        assert config.ai.api_key == '${TEST_API_KEY}'
    
    def test_ensure_directories_created(self, tmp_path):
        """Test that ensure_directories creates required directories."""
        config_data = {
            'ai': {'api_key': 'test-key'},
            'paths': {
                'data_dir': str(tmp_path / 'data'),
                'logs_dir': str(tmp_path / 'logs'),
                'dashboard_dir': str(tmp_path / 'dashboard'),
                'backup_dir': str(tmp_path / 'backups')
            }
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(str(config_file), load_env_file=False)
        
        # Directories should be created
        assert (tmp_path / 'data').exists()
        assert (tmp_path / 'logs').exists()
        assert (tmp_path / 'dashboard').exists()
        assert (tmp_path / 'backups').exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

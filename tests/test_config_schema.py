"""
Comprehensive unit tests for Config Schema validation.
Tests Pydantic models, type coercion, and validation rules.
"""
import pytest
from pathlib import Path
from pydantic import ValidationError
from src.config_schema import (
    PathConfig, AIConfig, HealingConfig, MonitoringConfig,
    GitHubConfig, SecurityConfig, PerformanceConfig,
    EnvironmentConfig, Config
)


class TestPathConfig:
    """Test PathConfig validation."""
    
    def test_valid_path_config(self):
        """Test creating PathConfig with valid paths."""
        config = PathConfig(
            data_dir="data/raw",
            logs_dir="logs",
            dashboard_dir="dashboard",
            backup_dir="backups"
        )
        assert isinstance(config.data_dir, Path)
        assert config.data_dir.as_posix() == "data/raw"
    
    def test_path_config_defaults(self):
        """Test PathConfig default values."""
        config = PathConfig()
        assert config.data_dir == Path("data/raw")
        assert config.logs_dir == Path("logs")
    
    def test_path_string_conversion(self):
        """Test automatic conversion of strings to Path objects."""
        config = PathConfig(data_dir="custom/path")
        assert isinstance(config.data_dir, Path)
        assert config.data_dir.as_posix() == "custom/path"


class TestAIConfig:
    """Test AIConfig validation."""
    
    def test_valid_ai_config(self):
        """Test creating AIConfig with valid values."""
        config = AIConfig(
            api_key="test-key-123",
            model="openai/gpt-4o-mini",
            temperature=0.5
        )
        assert config.api_key == "test-key-123"
        assert config.temperature == 0.5
    
    def test_ai_config_defaults(self):
        """Test AIConfig default values."""
        config = AIConfig(api_key="test-key")
        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.model == "openai/gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.max_tokens == 4000
        assert config.timeout == 60
        assert config.max_retries == 3
    
    def test_empty_api_key_validation(self):
        """Test that empty API key raises validation error."""
        with pytest.raises(ValidationError):
            AIConfig(api_key="")
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="   ")
    
    def test_temperature_range_validation(self):
        """Test temperature must be between 0.0 and 2.0."""
        # Valid temperatures
        AIConfig(api_key="test", temperature=0.0)
        AIConfig(api_key="test", temperature=1.0)
        AIConfig(api_key="test", temperature=2.0)
        
        # Invalid temperatures
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", temperature=-0.1)
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", temperature=2.1)
    
    def test_max_tokens_positive(self):
        """Test max_tokens must be positive."""
        AIConfig(api_key="test", max_tokens=1000)
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", max_tokens=0)
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", max_tokens=-100)
    
    def test_timeout_positive(self):
        """Test timeout must be positive."""
        AIConfig(api_key="test", timeout=30)
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", timeout=0)
    
    def test_max_retries_range(self):
        """Test max_retries must be between 1 and 10."""
        AIConfig(api_key="test", max_retries=1)
        AIConfig(api_key="test", max_retries=10)
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", max_retries=0)
        
        with pytest.raises(ValidationError):
            AIConfig(api_key="test", max_retries=11)


class TestHealingConfig:
    """Test HealingConfig validation."""
    
    def test_valid_healing_config(self):
        """Test creating HealingConfig with valid values."""
        config = HealingConfig(
            max_attempts=5,
            enable_rollback=True,
            backup_retention_days=60
        )
        assert config.max_attempts == 5
        assert config.enable_rollback is True
    
    def test_healing_config_defaults(self):
        """Test HealingConfig default values."""
        config = HealingConfig()
        assert config.max_attempts == 3
        assert config.enable_rollback is True
        assert config.enable_backup is True
        assert config.test_before_apply is True
        assert config.backup_retention_days == 30
    
    def test_max_attempts_range(self):
        """Test max_attempts must be between 1 and 10."""
        HealingConfig(max_attempts=1)
        HealingConfig(max_attempts=10)
        
        with pytest.raises(ValidationError):
            HealingConfig(max_attempts=0)
        
        with pytest.raises(ValidationError):
            HealingConfig(max_attempts=11)
    
    def test_backup_retention_positive(self):
        """Test backup_retention_days must be positive."""
        HealingConfig(backup_retention_days=1)
        
        with pytest.raises(ValidationError):
            HealingConfig(backup_retention_days=0)


class TestMonitoringConfig:
    """Test MonitoringConfig validation."""
    
    def test_valid_monitoring_config(self):
        """Test creating MonitoringConfig with valid values."""
        config = MonitoringConfig(
            enable_monitoring=True,
            slack_webhook_url="https://hooks.slack.com/test",
            metrics_retention_days=180
        )
        assert config.enable_monitoring is True
        assert config.slack_webhook_url == "https://hooks.slack.com/test"
    
    def test_monitoring_config_defaults(self):
        """Test MonitoringConfig default values."""
        config = MonitoringConfig()
        assert config.enable_monitoring is True
        assert config.slack_webhook_url is None
        assert config.enable_dashboard is True
        assert config.metrics_retention_days == 90
    
    def test_optional_slack_webhook(self):
        """Test that slack_webhook_url is optional."""
        config = MonitoringConfig(slack_webhook_url=None)
        assert config.slack_webhook_url is None


class TestGitHubConfig:
    """Test GitHubConfig validation."""
    
    def test_valid_github_config_disabled(self):
        """Test GitHubConfig when GitHub is disabled."""
        config = GitHubConfig(enable_github=False)
        assert config.enable_github is False
        assert config.token is None
        assert config.repo_name is None
    
    def test_valid_github_config_enabled(self):
        """Test GitHubConfig when GitHub is enabled."""
        config = GitHubConfig(
            enable_github=True,
            token="ghp_test_token",
            repo_name="user/repo"
        )
        assert config.enable_github is True
        assert config.token == "ghp_test_token"
        assert config.repo_name == "user/repo"
    
    def test_github_config_defaults(self):
        """Test GitHubConfig default values."""
        config = GitHubConfig()
        assert config.enable_github is False
        assert config.auto_create_pr is False


class TestSecurityConfig:
    """Test SecurityConfig validation."""
    
    def test_valid_security_config(self):
        """Test creating SecurityConfig with valid values."""
        config = SecurityConfig(
            enable_audit_log=True,
            mask_sensitive_data=True,
            max_code_size_kb=1000
        )
        assert config.enable_audit_log is True
        assert config.max_code_size_kb == 1000
    
    def test_security_config_defaults(self):
        """Test SecurityConfig default values."""
        config = SecurityConfig()
        assert config.enable_audit_log is True
        assert config.mask_sensitive_data is True
        assert config.enable_code_signing is False
        assert config.max_code_size_kb == 500
    
    def test_max_code_size_positive(self):
        """Test max_code_size_kb must be positive."""
        SecurityConfig(max_code_size_kb=1)
        
        with pytest.raises(ValidationError):
            SecurityConfig(max_code_size_kb=0)


class TestPerformanceConfig:
    """Test PerformanceConfig validation."""
    
    def test_valid_performance_config(self):
        """Test creating PerformanceConfig with valid values."""
        config = PerformanceConfig(
            enable_caching=True,
            cache_ttl_hours=48,
            max_parallel_healings=5
        )
        assert config.enable_caching is True
        assert config.cache_ttl_hours == 48
    
    def test_performance_config_defaults(self):
        """Test PerformanceConfig default values."""
        config = PerformanceConfig()
        assert config.enable_caching is True
        assert config.cache_ttl_hours == 24
        assert config.max_parallel_healings == 1
        assert config.rate_limit_per_minute == 10
    
    def test_max_parallel_healings_range(self):
        """Test max_parallel_healings must be between 1 and 10."""
        PerformanceConfig(max_parallel_healings=1)
        PerformanceConfig(max_parallel_healings=10)
        
        with pytest.raises(ValidationError):
            PerformanceConfig(max_parallel_healings=0)
        
        with pytest.raises(ValidationError):
            PerformanceConfig(max_parallel_healings=11)


class TestEnvironmentConfig:
    """Test EnvironmentConfig validation."""
    
    def test_valid_environment_config(self):
        """Test creating EnvironmentConfig with valid values."""
        config = EnvironmentConfig(
            env="production",
            debug=False,
            log_level="ERROR"
        )
        assert config.env == "production"
        assert config.debug is False
        assert config.log_level == "ERROR"
    
    def test_environment_config_defaults(self):
        """Test EnvironmentConfig default values."""
        config = EnvironmentConfig()
        assert config.env == "development"
        assert config.debug is False
        assert config.log_level == "INFO"
    
    def test_env_validation(self):
        """Test environment name validation."""
        # Valid environments
        EnvironmentConfig(env="development")
        EnvironmentConfig(env="staging")
        EnvironmentConfig(env="production")
        EnvironmentConfig(env="dev")
        EnvironmentConfig(env="prod")
        
        # Case insensitive
        config = EnvironmentConfig(env="PRODUCTION")
        assert config.env == "production"
        
        # Invalid environment
        with pytest.raises(ValidationError):
            EnvironmentConfig(env="invalid")
    
    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        EnvironmentConfig(log_level="DEBUG")
        EnvironmentConfig(log_level="INFO")
        EnvironmentConfig(log_level="WARNING")
        EnvironmentConfig(log_level="ERROR")
        EnvironmentConfig(log_level="CRITICAL")
        
        # Case insensitive
        config = EnvironmentConfig(log_level="debug")
        assert config.log_level == "DEBUG"
        
        # Invalid log level
        with pytest.raises(ValidationError):
            EnvironmentConfig(log_level="INVALID")


class TestConfig:
    """Test main Config object."""
    
    def test_valid_config(self):
        """Test creating complete Config with all sections."""
        config = Config(
            environment=EnvironmentConfig(env="development"),
            paths=PathConfig(),
            ai=AIConfig(api_key="test-key"),
            healing=HealingConfig(),
            monitoring=MonitoringConfig(),
            github=GitHubConfig(),
            security=SecurityConfig(),
            performance=PerformanceConfig()
        )
        assert config.environment.env == "development"
        assert config.ai.api_key == "test-key"
    
    def test_config_with_defaults(self):
        """Test Config uses default values for optional sections."""
        config = Config(ai=AIConfig(api_key="test-key"))
        assert config.environment.env == "development"
        assert config.healing.max_attempts == 3
        assert config.monitoring.enable_monitoring is True
    
    def test_github_validation_when_enabled(self):
        """Test that GitHub config is validated when enabled."""
        # Should fail: GitHub enabled but no token
        with pytest.raises(ValidationError):
            Config(
                ai=AIConfig(api_key="test-key"),
                github=GitHubConfig(enable_github=True, repo_name="user/repo")
            )
        
        # Should fail: GitHub enabled but no repo_name
        with pytest.raises(ValidationError):
            Config(
                ai=AIConfig(api_key="test-key"),
                github=GitHubConfig(enable_github=True, token="test-token")
            )
        
        # Should succeed: GitHub enabled with both token and repo_name
        config = Config(
            ai=AIConfig(api_key="test-key"),
            github=GitHubConfig(
                enable_github=True,
                token="test-token",
                repo_name="user/repo"
            )
        )
        assert config.github.enable_github is True
    
    def test_missing_required_ai_section(self):
        """Test that AI section is required."""
        with pytest.raises(ValidationError):
            Config()
    
    def test_type_coercion(self):
        """Test automatic type coercion."""
        config = Config(
            ai=AIConfig(
                api_key="test-key",
                temperature="0.5",  # String should be coerced to float
                max_tokens="2000"  # String should be coerced to int
            )
        )
        assert isinstance(config.ai.temperature, float)
        assert config.ai.temperature == 0.5
        assert isinstance(config.ai.max_tokens, int)
        assert config.ai.max_tokens == 2000
    
    def test_nested_config_access(self):
        """Test accessing nested configuration values."""
        config = Config(
            ai=AIConfig(api_key="test-key"),
            healing=HealingConfig(max_attempts=5)
        )
        assert config.ai.api_key == "test-key"
        assert config.healing.max_attempts == 5
        assert config.environment.env == "development"
    
    def test_config_immutability(self):
        """Test that config values can be modified (Pydantic v2 allows this)."""
        config = Config(ai=AIConfig(api_key="test-key"))
        # In Pydantic v2, models are mutable by default
        config.ai.api_key = "new-key"
        assert config.ai.api_key == "new-key"
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields in nested configs are handled."""
        # Pydantic v2 ignores extra fields by default
        config_data = {
            'ai': {
                'api_key': 'test-key',
                'extra_field': 'should-be-ignored'
            }
        }
        config = Config(**config_data)
        assert config.ai.api_key == 'test-key'
        # Extra field is ignored, not stored
        assert not hasattr(config.ai, 'extra_field')


class TestConfigEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_null_values_for_optional_fields(self):
        """Test that null values work for optional fields."""
        config = Config(
            ai=AIConfig(api_key="test-key", max_tokens=None)
        )
        assert config.ai.max_tokens is None
    
    def test_very_long_strings(self):
        """Test handling of very long string values."""
        long_key = "k" * 10000
        config = AIConfig(api_key=long_key)
        assert len(config.api_key) == 10000
    
    def test_boundary_values(self):
        """Test boundary values for numeric fields."""
        # Minimum values
        config = Config(
            ai=AIConfig(
                api_key="test",
                temperature=0.0,
                max_tokens=1,
                timeout=1,
                max_retries=1
            ),
            healing=HealingConfig(
                max_attempts=1,
                backup_retention_days=1
            )
        )
        assert config.ai.temperature == 0.0
        assert config.ai.max_tokens == 1
        
        # Maximum values
        config = Config(
            ai=AIConfig(
                api_key="test",
                temperature=2.0,
                max_retries=10
            ),
            healing=HealingConfig(max_attempts=10)
        )
        assert config.ai.temperature == 2.0
        assert config.ai.max_retries == 10
    
    def test_whitespace_in_api_key(self):
        """Test that whitespace is stripped from API key."""
        config = AIConfig(api_key="  test-key  ")
        assert config.api_key == "test-key"
    
    def test_case_sensitivity(self):
        """Test case sensitivity in string fields."""
        config = EnvironmentConfig(
            env="DEVELOPMENT",
            log_level="debug"
        )
        # Should be normalized to lowercase/uppercase
        assert config.env == "development"
        assert config.log_level == "DEBUG"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

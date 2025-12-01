"""
Configuration Manager for loading and managing application configuration.
Supports YAML files, environment variables, and environment-specific configs.
"""
import yaml
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.config_schema import Config
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Singleton configuration manager that loads and manages application configuration.
    
    Supports:
    - YAML configuration files
    - Environment-specific configs (dev/staging/prod)
    - Environment variable overrides
    - Secrets management
    """
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Config] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the config manager (only once due to singleton)."""
        if self._config is None:
            # Don't auto-load in __init__ to allow explicit loading
            pass
    
    def load_config(
        self,
        config_path: Optional[str] = None,
        env: Optional[str] = None,
        load_env_file: bool = True
    ) -> Config:
        """
        Load configuration from YAML file and environment variables.
        
        Args:
            config_path: Path to main config file (default: config/config.yaml)
            env: Environment name (development/staging/production)
            load_env_file: Whether to load .env file
            
        Returns:
            Config object with all settings
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        # Load .env file if requested
        if load_env_file:
            env_file = Path('.env')
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"Loaded environment variables from {env_file}")
        
        # Determine config file path
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)
        
        # Load base configuration
        base_config = self._load_yaml_file(config_path)
        
        # Determine environment
        if env is None:
            env = os.getenv('ENVIRONMENT', os.getenv('ENV', 'development'))
        
        # Load environment-specific config if exists
        env_config_path = config_path.parent / f"config.{env}.yaml"
        if env_config_path.exists():
            env_config = self._load_yaml_file(env_config_path)
            base_config = self._deep_merge(base_config, env_config)
            logger.info(f"Merged environment config from {env_config_path}")
        
        # Override with environment variables
        base_config = self._apply_env_overrides(base_config)
        
        # Validate and create Config object
        try:
            self._config = Config(**base_config)
            logger.info(f"Configuration loaded successfully for environment: {env}")
            
            # Ensure required directories exist
            self._config.ensure_directories()
            
            return self._config
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file and return as dictionary.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Dictionary with config data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data is None:
                    return {}
                return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading {file_path}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override taking precedence.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables should be prefixed with 'SHP_' (Self-Healing Pipeline)
        and use double underscores for nesting:
        - SHP_AI__API_KEY -> config['ai']['api_key']
        - SHP_HEALING__MAX_ATTEMPTS -> config['healing']['max_attempts']
        
        Args:
            config: Base configuration dictionary
            
        Returns:
            Configuration with environment overrides applied
        """
        prefix = 'SHP_'
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue
            
            # Remove prefix and split by double underscore
            key_path = env_key[len(prefix):].lower().split('__')
            
            # Navigate to the nested location
            current = config
            for i, key in enumerate(key_path[:-1]):
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value (convert types as needed)
            final_key = key_path[-1]
            current[final_key] = self._convert_env_value(env_value)
            
            logger.debug(f"Applied environment override: {env_key} -> {'.'.join(key_path)}")
        
        return config
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate Python type.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value (bool, int, float, or str)
        """
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get_config(self) -> Config:
        """
        Get the current configuration.
        
        Returns:
            Current Config object
            
        Raises:
            RuntimeError: If config hasn't been loaded yet
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config
    
    def reload_config(self, config_path: Optional[str] = None, env: Optional[str] = None) -> Config:
        """
        Reload configuration from files.
        
        Args:
            config_path: Path to config file
            env: Environment name
            
        Returns:
            Reloaded Config object
        """
        self._config = None
        return self.load_config(config_path, env)
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._config = None


# Convenience function for getting config
def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config object
        
    Raises:
        RuntimeError: If config hasn't been loaded
    """
    return ConfigManager().get_config()

"""
Configuration Schema Definitions using Pydantic for type-safe configuration management.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from pathlib import Path
import os


class PathConfig(BaseModel):
    """Path configuration for data and logs."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    data_dir: Path = Field(default=Path("data/raw"), description="Directory for raw data files")
    logs_dir: Path = Field(default=Path("logs"), description="Directory for log files")
    dashboard_dir: Path = Field(default=Path("dashboard"), description="Directory for dashboard files")
    backup_dir: Path = Field(default=Path("backups"), description="Directory for backup files")
    
    @field_validator('data_dir', 'logs_dir', 'dashboard_dir', 'backup_dir', mode='before')
    @classmethod
    def resolve_path(cls, v):
        """Convert string paths to Path objects and resolve them."""
        if isinstance(v, str):
            # Handle environment variables in paths
            v = os.path.expandvars(v)
            return Path(v)
        return v


class AIConfig(BaseModel):
    """AI/LLM configuration."""
    api_key: str = Field(..., description="API key for AI service")
    base_url: str = Field(default="https://openrouter.ai/api/v1", description="Base URL for AI API")
    model: str = Field(default="openai/gpt-4o-mini", description="Model to use for healing")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Temperature for AI responses")
    max_tokens: Optional[int] = Field(default=4000, gt=0, description="Maximum tokens in response")
    timeout: int = Field(default=60, gt=0, description="API timeout in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum API retry attempts")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Ensure API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("API key cannot be empty")
        return v.strip()


class HealingConfig(BaseModel):
    """Configuration for healing behavior."""
    max_attempts: int = Field(default=3, ge=1, le=10, description="Maximum healing attempts")
    enable_rollback: bool = Field(default=True, description="Enable automatic rollback on failure")
    enable_backup: bool = Field(default=True, description="Enable backup before healing")
    test_before_apply: bool = Field(default=True, description="Test fix before applying")
    backup_retention_days: int = Field(default=30, ge=1, description="Days to retain backups")
    
    
class MonitoringConfig(BaseModel):
    """Monitoring and alerting configuration."""
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    slack_webhook_url: Optional[str] = Field(default=None, description="Slack webhook URL for notifications")
    enable_dashboard: bool = Field(default=True, description="Enable HTML dashboard generation")
    metrics_retention_days: int = Field(default=90, ge=1, description="Days to retain metrics")
    alert_on_failure: bool = Field(default=True, description="Send alerts on healing failure")
    alert_on_success: bool = Field(default=False, description="Send alerts on healing success")
    

class GitHubConfig(BaseModel):
    """GitHub integration configuration."""
    enable_github: bool = Field(default=False, description="Enable GitHub integration")
    token: Optional[str] = Field(default=None, description="GitHub personal access token")
    repo_name: Optional[str] = Field(default=None, description="Repository name (username/repo)")
    auto_create_pr: bool = Field(default=False, description="Automatically create PRs for fixes")
    
    @field_validator('token', 'repo_name')
    @classmethod
    def validate_github_fields(cls, v, info):
        """Validate GitHub fields if GitHub is enabled."""
        # Note: This validator runs per-field, so we can't check enable_github here
        # That validation will be done at the Config level
        return v


class SecurityConfig(BaseModel):
    """Security and compliance configuration."""
    enable_audit_log: bool = Field(default=True, description="Enable audit logging")
    mask_sensitive_data: bool = Field(default=True, description="Mask sensitive data in logs")
    enable_code_signing: bool = Field(default=False, description="Enable code signing for AI fixes")
    max_code_size_kb: int = Field(default=500, ge=1, description="Maximum allowed code size in KB")
    

class PerformanceConfig(BaseModel):
    """Performance and scalability configuration."""
    enable_caching: bool = Field(default=True, description="Enable AI response caching")
    cache_ttl_hours: int = Field(default=24, ge=1, description="Cache TTL in hours")
    max_parallel_healings: int = Field(default=1, ge=1, le=10, description="Max parallel healing operations")
    rate_limit_per_minute: int = Field(default=10, ge=1, description="AI API rate limit per minute")


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    env: str = Field(default="development", description="Environment name (development/staging/production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    @field_validator('env')
    @classmethod
    def validate_env(cls, v):
        """Validate environment name."""
        allowed = ["development", "staging", "production", "dev", "prod"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()


class Config(BaseModel):
    """Main configuration object combining all sub-configurations."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    ai: AIConfig
    healing: HealingConfig = Field(default_factory=HealingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    @field_validator('github')
    @classmethod
    def validate_github_config(cls, v):
        """Validate GitHub configuration consistency."""
        if v.enable_github:
            if not v.token:
                raise ValueError("GitHub token is required when GitHub integration is enabled")
            if not v.repo_name:
                raise ValueError("GitHub repo_name is required when GitHub integration is enabled")
        return v
    
    def get_absolute_path(self, relative_path: Path) -> Path:
        """Convert relative path to absolute path based on project root."""
        if relative_path.is_absolute():
            return relative_path
        # Assume project root is parent of src directory
        project_root = Path(__file__).parent.parent
        return (project_root / relative_path).resolve()
    
    def ensure_directories(self):
        """Create all required directories if they don't exist."""
        for path_field in ['data_dir', 'logs_dir', 'dashboard_dir', 'backup_dir']:
            path = getattr(self.paths, path_field)
            abs_path = self.get_absolute_path(path)
            abs_path.mkdir(parents=True, exist_ok=True)

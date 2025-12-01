from src.config_schema import Config, AIConfig, PathConfig, HealingConfig, MonitoringConfig, GitHubConfig, SecurityConfig, PerformanceConfig, EnvironmentConfig
import traceback

try:
    config = Config(
        ai=AIConfig(api_key="dummy", model="dummy"),
        paths=PathConfig(),
        healing=HealingConfig(),
        monitoring=MonitoringConfig(slack_webhook_url="http://dummy-webhook"),
        github=GitHubConfig(),
        security=SecurityConfig(),
        performance=PerformanceConfig(),
        environment=EnvironmentConfig(env="test")
    )
    print("Config created successfully")
except Exception:
    traceback.print_exc()

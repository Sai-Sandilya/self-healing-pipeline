import pytest
import time
from unittest.mock import MagicMock, patch
from src.metrics import MetricsManager
from src.alert_manager import AlertManager
from src.config_schema import Config, MonitoringConfig

class TestMetricsManager:
    def test_singleton(self):
        m1 = MetricsManager()
        m2 = MetricsManager()
        assert m1 is m2

    def test_metrics_recording(self):
        metrics = MetricsManager()
        
        # Reset counters for test (Prometheus client doesn't easily allow reset, 
        # so we check if they increment)
        before = metrics.pipeline_runs.labels(status='success')._value.get()
        metrics.record_pipeline_run('success', 1.5)
        after = metrics.pipeline_runs.labels(status='success')._value.get()
        assert after == before + 1

        before_cost = metrics.ai_cost._value.get()
        metrics.record_cost(0.05)
        after_cost = metrics.ai_cost._value.get()
        assert after_cost == before_cost + 0.05

class TestAlertManager:
    def setup_method(self):
        # Create a minimal valid config
        # We need to mock the required fields or provide defaults
        # Assuming other fields have defaults or are optional, but let's be safe
        # We'll use a mock object for config to avoid Pydantic validation in this unit test
        # OR we construct it properly. Let's try constructing properly.
        
        from src.config_schema import AIConfig, PathConfig, HealingConfig, GitHubConfig, SecurityConfig, PerformanceConfig, EnvironmentConfig
        
        self.config = Config(
            ai=AIConfig(api_key="dummy", model="dummy"),
            paths=PathConfig(),
            healing=HealingConfig(),
            monitoring=MonitoringConfig(slack_webhook_url="http://dummy-webhook"),
            github=GitHubConfig(),
            security=SecurityConfig(),
            performance=PerformanceConfig(),
            environment=EnvironmentConfig(env="development")
        )
        self.alert_manager = AlertManager(self.config)

    @patch('requests.post')
    def test_send_alert(self, mock_post):
        mock_post.return_value.status_code = 200
        
        self.alert_manager.send_alert("Test Alert", "This is a test")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['json']['attachments'][0]['title'] == "Test Alert"

    @patch('requests.post')
    def test_deduplication(self, mock_post):
        mock_post.return_value.status_code = 200
        
        # First alert
        self.alert_manager.send_alert("Duplicate Alert", "First occurrence")
        assert mock_post.call_count == 1
        
        # Second alert (immediate) - should be suppressed
        self.alert_manager.send_alert("Duplicate Alert", "Second occurrence")
        assert mock_post.call_count == 1
        
        # Third alert (after window) - should be sent
        # We mock time.time to simulate passage of time
        with patch('time.time', return_value=time.time() + 301):
            self.alert_manager.send_alert("Duplicate Alert", "Third occurrence")
            assert mock_post.call_count == 2

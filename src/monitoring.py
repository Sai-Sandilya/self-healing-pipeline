import json
import time
from datetime import datetime
import os
import requests
from src.metrics import MetricsManager
from src.alert_manager import AlertManager

class MonitoringSystem:
    def __init__(self, config=None):
        self.config = config
        # Use config for paths if available, else defaults
        if config:
            self.metrics_file = config.monitoring.metrics_path
            self.dashboard_file = config.monitoring.dashboard_path
            self.alert_manager = AlertManager(config)
        else:
            self.metrics_file = r'E:\self_healing_pipeline\logs\metrics.json'
            self.dashboard_file = r'E:\self_healing_pipeline\logs\dashboard.html'
            # Dummy alert manager if no config
            from src.config_schema import Config
            self.alert_manager = AlertManager(Config())

        self.metrics_manager = MetricsManager()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        
        # Load existing history
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def log_error(self, error_msg):
        """Log an error occurrence."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ERROR',
            'message': error_msg
        }
        self.history.append(entry)
        self._save()
        
        # Prometheus
        self.metrics_manager.record_error('unknown') # We could parse type if needed
        
        # Alerting
        self.alert_manager.send_alert("Pipeline Error", error_msg, level="error")

    def log_healing_attempt(self, success, error_log, fix_code):
        """Log a healing attempt."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'HEALING',
            'success': success,
            'error': error_log,
            'fix': fix_code
        }
        self.history.append(entry)
        self._save()
        
        # Prometheus
        status = 'success' if success else 'failure'
        self.metrics_manager.record_healing(status)
        
        # Alerting
        if success:
            self.alert_manager.send_alert("Healing Successful", "AI successfully fixed the pipeline.", level="info")
        else:
            self.alert_manager.send_alert("Healing Failed", "AI attempted to fix the pipeline but failed.", level="error")

    def _save(self):
        with open(self.metrics_file, 'w') as f:
            json.dump(self.history, f, indent=2)
        self.generate_dashboard()

    def generate_dashboard(self):
        """Generate a simple HTML dashboard."""
        html = f"""
        <html>
        <head>
            <title>Pipeline Health Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .card {{ border: 1px solid #ccc; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
                .success {{ background-color: #d4edda; border-color: #c3e6cb; }}
                .error {{ background-color: #f8d7da; border-color: #f5c6cb; }}
                h1 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>Self-Healing Pipeline Dashboard</h1>
            <p>Last Updated: {datetime.now()}</p>
            <p><a href="http://localhost:8000/metrics">Prometheus Metrics</a></p>
            <hr>
            <h2>Recent Events</h2>
        """
        
        for event in reversed(self.history[-10:]):
            color_class = 'success' if event.get('success', False) or event['type'] == 'INFO' else 'error'
            html += f"""
            <div class="card {color_class}">
                <strong>{event['timestamp']}</strong> - {event['type']}<br>
                <pre>{event.get('message') or event.get('error')}</pre>
            </div>
            """
            
        html += "</body></html>"
        
        with open(self.dashboard_file, 'w') as f:
            f.write(html)

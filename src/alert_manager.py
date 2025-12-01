import time
import logging
import requests
from typing import Dict, Optional
from src.config_schema import Config

class AlertManager:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_alert_times: Dict[str, float] = {}
        self.deduplication_window = 300  # 5 minutes

    def send_alert(self, title: str, message: str, level: str = "error"):
        """
        Send an alert to configured channels (Slack, Log).
        Deduplicates alerts based on title.
        """
        # Deduplication check
        current_time = time.time()
        if title in self.last_alert_times:
            if current_time - self.last_alert_times[title] < self.deduplication_window:
                self.logger.info(f"Suppressed duplicate alert: {title}")
                return
        
        self.last_alert_times[title] = current_time
        
        # Log the alert
        log_msg = f"[{level.upper()}] {title}: {message}"
        if level == "error":
            self.logger.error(log_msg)
        else:
            self.logger.warning(log_msg)
            
        # Send to Slack if configured
        if self.config.monitoring and self.config.monitoring.slack_webhook_url:
            self._send_slack(title, message, level)

    def _send_slack(self, title: str, message: str, level: str):
        color = "#FF0000" if level == "error" else "#FFA500"
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": "Self-Healing Pipeline",
                    "ts": int(time.time())
                }
            ]
        }
        
        try:
            response = requests.post(
                self.config.monitoring.slack_webhook_url, 
                json=payload, 
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")

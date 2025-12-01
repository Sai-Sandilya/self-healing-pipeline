import json
import os
from datetime import datetime
import requests

class MonitoringSystem:
    def __init__(self, slack_webhook_url=None):
        self.slack_webhook_url = slack_webhook_url
        self.metrics_file = 'E:\\self_healing_pipeline\\logs\\metrics.json'
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        '''Load existing metrics or create new.'''
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            'total_failures': 0,
            'total_heals': 0,
            'successful_heals': 0,
            'failed_heals': 0,
            'healing_history': []
        }
    
    def _save_metrics(self):
        '''Save metrics to file.'''
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def record_failure(self, error_message):
        '''Record a pipeline failure.'''
        self.metrics['total_failures'] += 1
        print(f' Metrics: Total failures = {self.metrics[\"total_failures\"]}')
    
    def record_healing_attempt(self, success, attempts, error_log):
        '''Record a healing attempt.'''
        self.metrics['total_heals'] += 1
        if success:
            self.metrics['successful_heals'] += 1
        else:
            self.metrics['failed_heals'] += 1
        
        self.metrics['healing_history'].append({
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'attempts': attempts,
            'error': error_log[:200]  # Truncate for storage
        })
        
        self._save_metrics()
        
        # Calculate success rate
        success_rate = (self.metrics['successful_heals'] / self.metrics['total_heals'] * 100) if self.metrics['total_heals'] > 0 else 0
        print(f' Metrics: Success Rate = {success_rate:.1f}%')
        
        # Send Slack notification
        if success:
            self._send_slack_notification(f' Pipeline healed successfully in {attempts} attempt(s)!', 'good')
        else:
            self._send_slack_notification(f' Pipeline healing failed after {attempts} attempts.', 'danger')
    
    def _send_slack_notification(self, message, color='good'):
        '''Send notification to Slack.'''
        if not self.slack_webhook_url:
            print(f' Slack (Mock): {message}')
            return
        
        payload = {
            'attachments': [{
                'color': color,
                'text': message,
                'footer': 'Self-Healing Pipeline',
                'ts': int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(self.slack_webhook_url, json=payload)
            if response.status_code == 200:
                print(f' Slack notification sent: {message}')
            else:
                print(f' Slack notification failed: {response.status_code}')
        except Exception as e:
            print(f' Slack notification error: {e}')
    
    def generate_dashboard(self):
        '''Generate HTML dashboard.'''
        success_rate = (self.metrics['successful_heals'] / self.metrics['total_heals'] * 100) if self.metrics['total_heals'] > 0 else 0
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Self-Healing Pipeline Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        .metric {{ display: inline-block; margin: 20px; padding: 20px; background: #f9f9f9; border-radius: 4px; min-width: 200px; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #2196F3; }}
        .metric-label {{ color: #666; margin-top: 10px; }}
        .success {{ color: #4CAF50; }}
        .failure {{ color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2196F3; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1> Self-Healing Pipeline Dashboard</h1>
        
        <div class="metric">
            <div class="metric-value">{self.metrics['total_failures']}</div>
            <div class="metric-label">Total Failures</div>
        </div>
        
        <div class="metric">
            <div class="metric-value class="success">{self.metrics['successful_heals']}</div>
            <div class="metric-label">Successful Heals</div>
        </div>
        
        <div class="metric">
            <div class="metric-value class="failure">{self.metrics['failed_heals']}</div>
            <div class="metric-label">Failed Heals</div>
        </div>
        
        <div class="metric">
            <div class="metric-value">{success_rate:.1f}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        
        <h2>Recent Healing History</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Error (Truncated)</th>
            </tr>
'''
        
        for entry in reversed(self.metrics['healing_history'][-10:]):  # Last 10
            status = ' Success' if entry['success'] else ' Failed'
            html += f'''
            <tr>
                <td>{entry['timestamp']}</td>
                <td>{status}</td>
                <td>{entry['attempts']}</td>
                <td>{entry['error']}</td>
            </tr>
'''
        
        html += '''
        </table>
    </div>
</body>
</html>
'''
        
        dashboard_path = 'E:\\self_healing_pipeline\\dashboard\\index.html'
        with open(dashboard_path, 'w') as f:
            f.write(html)
        
        print(f' Dashboard generated: {dashboard_path}')
        return dashboard_path

if __name__ == '__main__':
    monitor = MonitoringSystem()
    monitor.generate_dashboard()

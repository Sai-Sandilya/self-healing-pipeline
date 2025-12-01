import subprocess
import sys
import os
from src.advanced_doctor import AdvancedDataDoctor
from src.monitoring import MonitoringSystem

def run_script(script_path):
    print(f'\n Running {os.path.basename(script_path)}...')
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f' Failed with error:\n{result.stderr}')
        return False, result.stderr
    return True, None

def main():
    print(' Starting Advanced Self-Healing Pipeline Simulation')
    print('=' * 60)
    print('Features: Multi-Attempt | Rollback | Monitoring | Dashboard')
    print('=' * 60)
    
    etl_script = r'E:\self_healing_pipeline\src\etl_pipeline.py'
    chaos_script = r'E:\self_healing_pipeline\src\chaos_monkey.py'
    data_path = r'E:\self_healing_pipeline\data\raw\users.csv'
    
    # API Key
    api_key = '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'
    
    # Initialize monitoring
    monitor = MonitoringSystem(slack_webhook_url=None)  # Set to your Slack webhook if available
    
    # 1. Inject Failure
    print('\n[Step 1] Injecting Failure...')
    success, _ = run_script(chaos_script)
    if not success:
        print('Chaos Monkey failed to run. Aborting.')
        return

    # 2. Run Pipeline (Expect Failure)
    print('\n[Step 2] Running Pipeline (Expecting Failure)...')
    success, error_log = run_script(etl_script)
    
    if success:
        print(' Pipeline succeeded unexpectedly!')
        return
    
    print(' Pipeline crashed as expected.')
    monitor.record_failure(error_log)
    
    # 3. Call the Advanced Doctor (Multi-Attempt with Rollback)
    print('\n[Step 3] Calling Advanced Data Doctor...')
    print('Features: 3 Retry Attempts | Feedback Loop | Auto-Rollback')
    
    doctor = AdvancedDataDoctor(api_key=api_key, max_attempts=3)
    healed = doctor.diagnose_and_heal(etl_script, data_path, error_log)
    
    # Record healing attempt
    attempts_used = 3 if not healed else 1  # Simplified for demo
    monitor.record_healing_attempt(healed, attempts_used, error_log)
    
    if healed:
        # 4. Retry Pipeline
        print('\n[Step 4] Retrying Pipeline...')
        success, _ = run_script(etl_script)
        if success:
            print('\n SUCCESS! Advanced healing completed.')
        else:
            print('\n Fix validation failed.')
    else:
        print('\n All healing attempts exhausted. Rollback completed.')
    
    # 5. Generate Dashboard
    print('\n[Step 5] Generating Dashboard...')
    dashboard_path = monitor.generate_dashboard()
    print(f'\n View dashboard at: file:///{dashboard_path}')

if __name__ == '__main__':
    main()

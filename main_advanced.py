import subprocess
import sys
import os
from pathlib import Path
from src.advanced_doctor import AdvancedDataDoctor
from src.monitoring import MonitoringSystem
from src.config_manager import ConfigManager

def run_script(script_path):
    print(f'\n✓ Running {os.path.basename(script_path)}...')
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f'✗ Failed with error:\n{result.stderr}')
        return False, result.stderr
    return True, None

def main():
    print('🚀 Starting Advanced Self-Healing Pipeline Simulation')
    print('=' * 70)
    print('Features: Multi-Attempt | Rollback | Monitoring | Dashboard')
    print('=' * 70)
    
    # Load configuration
    try:
        config_manager = ConfigManager()
        project_root = Path(__file__).parent
        config = config_manager.load_config(
            str(project_root / 'config' / 'config.yaml'),
            env=os.getenv('ENVIRONMENT', 'development')
        )
        print(f'📋 Configuration loaded: {config.environment.env} environment')
        print(f'🤖 AI Model: {config.ai.model}')
        print(f'🔄 Max Healing Attempts: {config.healing.max_attempts}')
        print(f'📊 Monitoring: {"Enabled" if config.monitoring.enable_monitoring else "Disabled"}')
        print('=' * 70)
    except Exception as e:
        print(f'❌ Failed to load configuration: {e}')
        print('💡 Make sure to set SHP_AI_API_KEY environment variable or create .env file')
        return
    
    # Get paths from config
    project_root = Path(__file__).parent
    etl_script = str(project_root / 'src' / 'etl_pipeline.py')
    chaos_script = str(project_root / 'src' / 'chaos_monkey.py')
    data_path = str(config.get_absolute_path(config.paths.data_dir) / 'users.csv')
    
    # Initialize monitoring
    monitor = MonitoringSystem(config=config)
    
    # 1. Inject Failure
    print('\n[Step 1] 💥 Injecting Failure...')
    success, _ = run_script(chaos_script)
    if not success:
        print('Chaos Monkey failed to run. Aborting.')
        return

    # 2. Run Pipeline (Expect Failure)
    print('\n[Step 2] 🔧 Running Pipeline (Expecting Failure)...')
    success, error_log = run_script(etl_script)
    
    if success:
        print('✓ Pipeline succeeded unexpectedly!')
        return
    
    print('✗ Pipeline crashed as expected.')
    monitor.record_failure(error_log)
    
    # 3. Call the Advanced Doctor (Multi-Attempt with Rollback)
    print('\n[Step 3] 🏥 Calling Advanced Data Doctor...')
    print(f'Features: {config.healing.max_attempts} Retry Attempts | Feedback Loop | Auto-Rollback')
    
    doctor = AdvancedDataDoctor(config=config)
    healed = doctor.diagnose_and_heal(etl_script, data_path, error_log)
    
    # Record healing attempt
    attempts_used = config.healing.max_attempts if not healed else 1  # Simplified for demo
    monitor.record_healing_attempt(healed, attempts_used, error_log)
    
    if healed:
        # 4. Retry Pipeline
        print('\n[Step 4] 🔄 Retrying Pipeline...')
        success, _ = run_script(etl_script)
        if success:
            print('\n✅ SUCCESS! Advanced healing completed.')
        else:
            print('\n❌ Fix validation failed.')
    else:
        print(f'\n❌ All {config.healing.max_attempts} healing attempts exhausted. Rollback completed.')
    
    # 5. Generate Dashboard
    if config.monitoring.enable_dashboard:
        print('\n[Step 5] 📊 Generating Dashboard...')
        dashboard_path = monitor.generate_dashboard()
        print(f'\n✓ View dashboard at: file:///{dashboard_path}')

if __name__ == '__main__':
    main()

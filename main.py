import subprocess
import sys
import os
from pathlib import Path
from src.doctor import DataDoctor
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
    print('🚀 Starting Self-Healing Pipeline Simulation (Real AI via OpenRouter)')
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
        print('✓ Pipeline succeeded unexpectedly! Is the data broken?')
        return
    
    print('✗ Pipeline crashed as expected.')
    
    # 3. Call the Doctor
    print('\n[Step 3] 🏥 Calling Data Doctor with Real AI...')
    doctor = DataDoctor(config=config)
    healed = doctor.diagnose_and_heal(etl_script, data_path, error_log)
    
    if healed:
        # 4. Retry Pipeline
        print('\n[Step 4] 🔄 Retrying Pipeline...')
        success, _ = run_script(etl_script)
        if success:
            print('\n✅ SUCCESS! The pipeline healed itself using AI and ran successfully.')
        else:
            print('\n❌ The fix did not work. Pipeline still failing.')
    else:
        print('\n❌ Doctor could not fix the issue.')

if __name__ == '__main__':
    main()

import subprocess
import sys
import os
from src.doctor import DataDoctor

def run_script(script_path):
    print(f'\n Running {os.path.basename(script_path)}...')
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f' Failed with error:\n{result.stderr}')
        return False, result.stderr
    return True, None

def main():
    print(' Starting Self-Healing Pipeline Simulation (Real AI via OpenRouter)')
    print('============================================')
    
    etl_script = r'E:\self_healing_pipeline\src\etl_pipeline.py'
    chaos_script = r'E:\self_healing_pipeline\src\chaos_monkey.py'
    data_path = r'E:\self_healing_pipeline\data\raw\users.csv'
    
    # API Key - OpenRouter format
    api_key = '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'
    
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
        print(' Pipeline succeeded unexpectedly! Is the data broken?')
        return
    
    print(' Pipeline crashed as expected.')
    
    # 3. Call the Doctor
    print('\n[Step 3] Calling Data Doctor with Real AI...')
    doctor = DataDoctor(api_key=api_key)
    healed = doctor.diagnose_and_heal(etl_script, data_path, error_log)
    
    if healed:
        # 4. Retry Pipeline
        print('\n[Step 4] Retrying Pipeline...')
        success, _ = run_script(etl_script)
        if success:
            print('\n SUCCESS! The pipeline healed itself using AI and ran successfully.')
        else:
            print('\n The fix did not work. Pipeline still failing.')
    else:
        print('\n Doctor could not fix the issue.')

if __name__ == '__main__':
    main()

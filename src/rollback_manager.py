import os
import shutil
import json
from datetime import datetime

class RollbackManager:
    def __init__(self, backup_dir='E:\\self_healing_pipeline\\logs\\backups'):
        self.backup_dir = backup_dir
        self.version_history_file = 'E:\\self_healing_pipeline\\logs\\version_history.json'
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self, file_path):
        '''Create a timestamped backup of the file before modification.'''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f'{filename}.{timestamp}.bak')
        
        shutil.copy2(file_path, backup_path)
        print(f' Backup created: {backup_path}')
        
        # Log to version history
        self._log_version(file_path, backup_path, 'backup')
        return backup_path
    
    def rollback(self, file_path, backup_path=None):
        '''Rollback to the most recent backup or a specific backup.'''
        if backup_path is None:
            # Find the most recent backup
            filename = os.path.basename(file_path)
            backups = [f for f in os.listdir(self.backup_dir) if f.startswith(filename)]
            if not backups:
                print(' No backups found for rollback.')
                return False
            backups.sort(reverse=True)
            backup_path = os.path.join(self.backup_dir, backups[0])
        
        shutil.copy2(backup_path, file_path)
        print(f' Rolled back to: {backup_path}')
        self._log_version(file_path, backup_path, 'rollback')
        return True
    
    def _log_version(self, file_path, backup_path, action):
        '''Log version changes to JSON file.'''
        history = []
        if os.path.exists(self.version_history_file):
            with open(self.version_history_file, 'r') as f:
                history = json.load(f)
        
        history.append({
            'timestamp': datetime.now().isoformat(),
            'file': file_path,
            'backup': backup_path,
            'action': action
        })
        
        with open(self.version_history_file, 'w') as f:
            json.dump(history, f, indent=2)

if __name__ == '__main__':
    # Test
    rm = RollbackManager()
    print('Rollback Manager initialized.')

#!/usr/bin/env python3
"""
Sync Mission Control tasks to GitHub
"""
import json
import subprocess
import os
from datetime import datetime

def sync_tasks_to_github():
    """Sync task updates to GitHub repository"""
    print("🔄 Syncing Mission Control tasks to GitHub...")
    
    # Change to tasks directory
    os.chdir('/home/ubuntu/.openclaw/workspace/tasks')
    
    try:
        # Copy current tasks to data directory
        subprocess.run(['cp', 'tasks.json', 'data/tasks.json'], check=True)
        
        # Check if there are any changes
        result = subprocess.run(['git', 'diff', '--quiet', 'data/tasks.json'], 
                              capture_output=True)
        
        if result.returncode != 0:  # Changes detected
            print("📝 Task changes detected, committing to GitHub...")
            
            # Add the updated file
            subprocess.run(['git', 'add', 'data/tasks.json'], check=True)
            
            # Create commit with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            commit_msg = f"📊 Task update - {timestamp}"
            
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push to GitHub
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            print("✅ Tasks synced successfully to GitHub!")
            print("🌐 Live at: https://glitch-executor.github.io/mission-control/")
            
        else:
            print("✅ No task changes to sync")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Sync failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    sync_tasks_to_github()
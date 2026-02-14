#!/usr/bin/env python3
"""
⚡ Glitch Mission Control - Dashboard Server
Serves the autonomous task management dashboard locally
"""

import http.server
import socketserver
import json
import os
import webbrowser
from datetime import datetime

# Configuration
PORT = 8080
DASHBOARD_DIR = "/home/ubuntu/.openclaw/workspace/tasks"

class TaskDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Enhanced HTTP handler for task dashboard with live data"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)
    
    def do_GET(self):
        """Handle GET requests with task data injection"""
        
        if self.path == '/api/tasks':
            # API endpoint for live task data
            self.serve_task_api()
        elif self.path == '/api/stats':
            # API endpoint for dashboard stats
            self.serve_stats_api()
        else:
            # Serve static files
            super().do_GET()
    
    def serve_task_api(self):
        """Serve current task data as JSON"""
        try:
            tasks_file = os.path.join(DASHBOARD_DIR, 'tasks.json')
            if os.path.exists(tasks_file):
                with open(tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                
                # Add computed fields
                for task in tasks_data.get('tasks', []):
                    # Calculate progress percentage
                    subtasks = task.get('subtasks', [])
                    if subtasks:
                        completed = sum(1 for st in subtasks if st.get('done', False))
                        task['progressPercent'] = round((completed / len(subtasks)) * 100)
                    else:
                        task['progressPercent'] = 0
                
                self.send_json_response(tasks_data)
            else:
                self.send_json_response({'tasks': []})
        except Exception as e:
            self.send_error_response(f"Error loading tasks: {str(e)}")
    
    def serve_stats_api(self):
        """Serve dashboard statistics"""
        try:
            tasks_file = os.path.join(DASHBOARD_DIR, 'tasks.json')
            stats = {
                'backlog': 0,
                'in_progress': 0, 
                'review': 0,
                'done': 0,
                'total': 0,
                'lastUpdate': datetime.now().isoformat()
            }
            
            if os.path.exists(tasks_file):
                with open(tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                
                for task in tasks_data.get('tasks', []):
                    status = task.get('status', 'backlog')
                    if status in stats:
                        stats[status] += 1
                    stats['total'] += 1
            
            self.send_json_response(stats)
        except Exception as e:
            self.send_error_response(f"Error calculating stats: {str(e)}")
    
    def send_json_response(self, data):
        """Send JSON response with proper headers"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def send_error_response(self, error_msg):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_data = {'error': error_msg, 'timestamp': datetime.now().isoformat()}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))

def main():
    """Start the dashboard server"""
    os.chdir(DASHBOARD_DIR)
    
    with socketserver.TCPServer(("", PORT), TaskDashboardHandler) as httpd:
        print(f"⚡ Glitch Mission Control Dashboard")
        print(f"🚀 Server starting on http://localhost:{PORT}")
        print(f"📁 Serving from: {DASHBOARD_DIR}")
        print(f"🔄 Auto-refresh enabled (30s)")
        print(f"🎯 API endpoints: /api/tasks, /api/stats")
        print(f"💻 Press Ctrl+C to stop")
        
        # Auto-open browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
            print(f"🌐 Dashboard opened in browser")
        except:
            print(f"🌐 Open http://localhost:{PORT} in your browser")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n⚡ Dashboard server stopped")

if __name__ == "__main__":
    main()
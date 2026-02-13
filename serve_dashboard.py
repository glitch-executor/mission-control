#!/usr/bin/env python3
"""
Simple HTTP server for Mission Control Kanban Dashboard
"""
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class TaskDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the main dashboard
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('kanban-dashboard.html', 'rb') as f:
                self.wfile.write(f.read())
        
        elif parsed_path.path == '/api/tasks':
            # Serve tasks JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open('tasks.json', 'rb') as f:
                self.wfile.write(f.read())
        
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/tasks':
            # Handle task updates
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                task_data = json.loads(post_data.decode('utf-8'))
                
                # Load current tasks
                with open('tasks.json', 'r') as f:
                    data = json.load(f)
                
                # Update or add task
                task_found = False
                for i, task in enumerate(data['tasks']):
                    if task['id'] == task_data['id']:
                        data['tasks'][i] = task_data
                        task_found = True
                        break
                
                if not task_found:
                    data['tasks'].append(task_data)
                
                # Save updated tasks
                with open('tasks.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())
        
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    PORT = 8080
    os.chdir('/home/ubuntu/.openclaw/workspace/tasks')
    
    with socketserver.TCPServer(("", PORT), TaskDashboardHandler) as httpd:
        print(f"🎛️ Mission Control Dashboard serving at http://localhost:{PORT}")
        print(f"📋 Task management interface ready")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")
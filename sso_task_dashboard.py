#!/usr/bin/env python3
"""
SSO-Protected Task Dashboard Server
Mission Control Kanban interface with GLITCH EXECUTOR authentication
"""
import http.server
import socketserver
import json
import os
import requests
from urllib.parse import urlparse, parse_qs, parse_qsl
from datetime import datetime

class SSOTaskDashboardHandler(http.server.SimpleHTTPRequestHandler):
    
    def check_sso_auth(self):
        """Validate SSO session with main auth server"""
        cookies = self.headers.get('Cookie', '')
        
        # Extract sso_session cookie
        sso_session = None
        for cookie in cookies.split(';'):
            cookie = cookie.strip()
            if cookie.startswith('sso_session='):
                sso_session = cookie.split('=', 1)[1]
                break
        
        if not sso_session:
            return None
            
        try:
            # Validate with main auth server
            response = requests.get(
                'https://glitchexecutor.com/auth/validate',
                cookies={'sso_session': sso_session},
                timeout=5,
                verify=False  # For development
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    return data.get('user')
            
        except Exception as e:
            print(f"Auth check failed: {e}")
        
        return None
    
    def redirect_to_login(self):
        """Redirect to SSO login"""
        from urllib.parse import quote
        current_url = f"https://task.glitchexecutor.com{self.path}"
        login_url = f"https://glitchexecutor.com?next={quote(current_url)}"
        
        self.send_response(302)
        self.send_header('Location', login_url)
        self.end_headers()
        
    def do_GET(self):
        # Check authentication first
        user = self.check_sso_auth()
        if not user:
            self.redirect_to_login()
            return
            
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the main dashboard with user info
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Inject user info into the dashboard HTML
            with open('kanban-dashboard.html', 'r') as f:
                html_content = f.read()
            
            # Replace title and add user info
            html_content = html_content.replace(
                'Mission Control - MoltBot',
                f'⚡ GLITCH EXECUTOR - Mission Control'
            )
            
            # Add user info to the header (simple injection)
            user_info = f'''
            <div class="user-info" style="position: fixed; top: 10px; right: 20px; z-index: 1000; 
                 background: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 8px; 
                 font-size: 14px;">
                👤 {user['username']} [{user.get('role', 'user')}]
                <button onclick="logout()" style="margin-left: 10px; padding: 4px 8px; 
                        background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Logout
                </button>
            </div>
            <script>
                function logout() {{
                    fetch('https://glitchexecutor.com/logout', {{ 
                        method: 'POST', 
                        credentials: 'include' 
                    }}).then(() => {{
                        window.location.href = 'https://glitchexecutor.com';
                    }});
                }}
            </script>
            '''
            
            html_content = html_content.replace('<body>', f'<body>\n{user_info}')
            
            self.wfile.write(html_content.encode())
        
        elif parsed_path.path == '/api/tasks':
            # Serve tasks JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open('tasks.json', 'rb') as f:
                self.wfile.write(f.read())
        
        else:
            # Handle other static files
            super().do_GET()
    
    def do_POST(self):
        # Check authentication first
        user = self.check_sso_auth()
        if not user:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Authentication required"}')
            return
            
        if self.path == '/api/tasks':
            # Handle task updates
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                task_data = json.loads(post_data.decode('utf-8'))
                
                # Add user info to the update
                task_data['lastUpdatedBy'] = user['username']
                task_data['lastUpdatedAt'] = datetime.now().isoformat()
                
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
                
                print(f"📝 Task updated by {user['username']}: {task_data.get('title', task_data['id'])}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
                
            except Exception as e:
                print(f"Error updating task: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())
        
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    PORT = 8082
    os.chdir('/home/ubuntu/.openclaw/workspace/tasks')
    
    with socketserver.TCPServer(("", PORT), SSOTaskDashboardHandler) as httpd:
        print(f"🎛️ GLITCH EXECUTOR Mission Control (SSO Protected)")
        print(f"📋 Dashboard serving at https://task.glitchexecutor.com")
        print(f"🔒 Authentication: Cross-subdomain SSO enabled")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Mission Control dashboard stopped")
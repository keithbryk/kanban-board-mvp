#!/usr/bin/env python3
"""Simple HTTP server for Kanban with CORS"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import http.server
import socketserver

PORT = 8080
KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}

class KanbanHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors(self):
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            path = '/index-pipeline.html'
        else:
            path = self.path
        
        path = path.split('?')[0]  # Remove query string
        
        fpath = Path("/home/kbryk/kanban" + path)
        if fpath.is_file():
            self.send_response(200)
            if path.endswith('.json'):
                self.send_header('Content-Type', 'application/json')
            else:
                self.send_header('Content-Type', 'text/html')
            self._send_cors()
            self.end_headers()
            with open(fpath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self._send_cors()
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_PUT(self):
        if self.path.startswith('/kanban'):
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
            try:
                data = json.loads(body)
                with open(KANBAN_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._send_cors()
                self.end_headers()
                self.wfile.write(b'{"success": true}')
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self._send_cors()
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/move':
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
            try:
                body_json = json.loads(body)
                task_id = body_json.get('taskId')
                to_column = body_json.get('toColumn')
                
                with open(KANBAN_FILE) as f:
                    data = json.load(f)
                
                now = datetime.now(timezone.utc).isoformat()
                
                for col in data['columns']:
                    for i, t in enumerate(col['tasks']):
                        if t.get('id') == task_id:
                            from_col = col['id']
                            task = col['tasks'].pop(i)
                            task['column'] = to_column
                            task['movedAt'] = now
                            if to_column == 'dev':
                                task['movedToDevAt'] = now
                            elif to_column == 'review':
                                task['movedToReviewAt'] = now
                            elif to_column == 'done':
                                task['completedAt'] = now
                                task['done'] = True
                            
                            task['activity'].append({
                                "timestamp": now,
                                "action": "moved",
                                "from": from_col,
                                "to": to_column,
                                "command": "UI button"
                            })
                            
                            for target_col in data['columns']:
                                if target_col['id'] == to_column:
                                    target_col['tasks'].append(task)
                                    break
                            break
                
                with open(KANBAN_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._send_cors()
                self.end_headers()
                self.wfile.write(b'{"success": true}')
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self._send_cors()
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[Kanban] {args[0]}")

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReuseAddrTCPServer(("", PORT), KanbanHandler) as httpd:
        print(f"🚀 Kanban at http://localhost:{PORT}")
        httpd.serve_forever()
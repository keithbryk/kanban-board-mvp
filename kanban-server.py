#!/usr/bin/env python3
"""HTTP server for Kanban with CORS support"""
import json
import http.server
import socketserver
from pathlib import Path

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
        path = self.path.split('?')[0]
        if path == '/' or path == '/index.html':
            path = '/index-pipeline.html'
        
        fpath = Path("/home/kbryk/kanban" + path)
        if fpath.is_file():
            self.send_response(200)
            self.send_header('Content-Type', 'application/json' if path.endswith('.json') else 'text/html')
            self._send_cors()
            self.end_headers()
            with open(fpath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self._send_cors()
            self.end_headers()
    
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
    
    def log_message(self, format, *args):
        pass

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReuseAddrTCPServer(("", PORT), KanbanHandler) as httpd:
        print(f"Kanban at http://0.0.0.0:{PORT}")
        httpd.serve_forever()
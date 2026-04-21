#!/usr/bin/env python3
"""Simple file server with CORS"""
import http.server
import socketserver
import os

PORT = 8765
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

os.chdir("/home/kbryk/kanban")

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

with ReuseAddrTCPServer(("", PORT), Handler) as httpd:
    print(f"Server at http://localhost:{PORT}")
    httpd.serve_forever()
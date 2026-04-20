#!/usr/bin/env python3
import http.server
import socketserver
import json
from pathlib import Path

KANBAN_FILE = Path("kanban.json")

class KanbanHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/tasks":
            with open(KANBAN_FILE) as f:
                data = json.load(f)
            tasks = []
            for col in data.get("columns", []):
                for task in col.get("tasks", []):
                    tasks.append({
                        "id": task.get("id"),
                        "text": task.get("text"),
                        "column": col["id"],
                        "done": task.get("done", False),
                        "notes": task.get("notes", ""),
                        "createdAt": task.get("createdAt", "")
                    })
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"tasks": tasks}).encode())
        elif self.path == "/app.js":
            with open("app.js") as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.end_headers()
            self.wfile.write(content.encode())
        elif self.path == "/":
            with open("index.html") as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode())
        else:
            self.send_error(404)

if __name__ == "__main__":
    server = socketserver.TCPServer(("", 8081), KanbanHandler)
    print("🚀 Kanban Board running at http://localhost:8081")
    server.serve_forever()
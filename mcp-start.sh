#!/bin/bash
cd /home/kbryk
/home/kbryk/mcp-venv/bin/python3 /home/kbryk/mcp-servers/kanban_server.py > /tmp/kanban-mcp.log 2>&1 &
sleep 2
echo "MCP server started, checking..."
tail -10 /tmp/kanban-mcp.log
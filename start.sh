#!/bin/bash
cd /home/kbryk/kanban
python3 kanban-api.py > /tmp/kanban.log 2>&1 &
sleep 2
echo "Server started, checking..."
curl -I http://localhost:8081
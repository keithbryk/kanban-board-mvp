#!/usr/bin/env python3
"""Test move functionality"""
import sys
sys.path.insert(0, '/home/kbryk/kanban')
from kanban-api-enhanced import move_task, add_task, get_task_history

# Test move task
print("Testing move_task...")
result = move_task(4, "dev", "From ideation to dev for pipeline testing")
print(f"Move result: {result}")

# Test add task
print("\nTesting add_task...")
result = add_task("Test new task from pipeline", "definition", "Testing the enhanced API with !move:dev command")
print(f"Add result: {result}")

# Test history
print("\nTesting get_task_history...")
result = get_task_history(4)
print(f"History: {result}")
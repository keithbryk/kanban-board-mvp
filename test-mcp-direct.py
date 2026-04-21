#!/usr/bin/env python3
"""Direct test of Kanban MCP tools without stdio protocol"""
import os
import json

KANBAN_FILE = os.path.expanduser("/home/kbryk/kanban/kanban.json")

def test_kanban_get_tasks():
    """Test get all tasks"""
    print("\n=== TEST: kanban_get_tasks ===")
    if not os.path.exists(KANBAN_FILE):
        print("❌ Kanban file not found")
        return

    with open(KANBAN_FILE) as f:
        kanban = json.load(f)

    tasks_list = []
    for col in kanban["columns"]:
        for task in col["tasks"]:
            tasks_list.append({
                "id": task["id"],
                "text": task.get("text", ""),
                "column": col["id"],
                "done": task.get("done", False),
                "createdAt": task.get("createdAt", "")
            })

    print(json.dumps({"tasks": tasks_list}, indent=2))
    print(f"\n✅ Found {len(tasks_list)} tasks")

def test_kanban_add_task():
    """Test add new task"""
    print("\n=== TEST: kanban_add_task ===")
    if not os.path.exists(KANBAN_FILE):
        print("❌ Kanban file not found")
        return

    with open(KANBAN_FILE) as f:
        kanban = json.load(f)

    # Find highest ID
    all_tasks = []
    for col in kanban["columns"]:
        all_tasks.extend(col["tasks"])

    new_id = max([t.get("id", 0) for t in all_tasks], default=0) + 1

    new_task = {
        "id": new_id,
        "text": "MCP Test Task",
        "column": "todo",
        "done": False,
        "createdAt": __import__("datetime").datetime.now().isoformat()
    }

    for col in kanban["columns"]:
        if col["id"] == "todo":
            col["tasks"].append(new_task)
            break

    # Save
    with open(KANBAN_FILE, "w") as f:
        json.dump(kanban, f, indent=2)

    print(json.dumps({"status": "created", "task": new_task}, indent=2))
    print("✅ Task created")

def test_kanban_move_task():
    """Test move task"""
    print("\n=== TEST: kanban_move_task ===")
    if not os.path.exists(KANBAN_FILE):
        print("❌ Kanban file not found")
        return

    with open(KANBAN_FILE) as f:
        kanban = json.load(f)

    # Find a task to move
    for col in kanban["columns"]:
        task = next((t for t in col["tasks"] if t.get("id") == 5), None)
        if task:
            old_column = col["id"]
            task["column"] = "done"
            col["tasks"].remove(task)

            for target_col in kanban["columns"]:
                if target_col["id"] == "done":
                    target_col["tasks"].append(task)
                    break

            with open(KANBAN_FILE, "w") as f:
                json.dump(kanban, f, indent=2)

            print(json.dumps({"status": "moved", "from": old_column, "to": "done"}, indent=2))
            print("✅ Task moved")
            return

    print("⚠️  No task with ID 5 found to move")

if __name__ == "__main__":
    print("Testing Kanban MCP Integration")
    print("=" * 50)

    # Test 1: Get tasks
    test_kanban_get_tasks()

    # Test 2: Add task
    test_kanban_add_task()

    # Test 3: Move task
    test_kanban_move_task()

    # Test 4: Get tasks again
    test_kanban_get_tasks()

    print("\n" + "=" * 50)
    print("✅ All tests completed!")
#!/usr/bin/env python3
"""
Auto-Queue Approved Tasks and Track Progress
Automatically moves approved tasks to Dev column and tracks completion
"""
import json
from pathlib import Path

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")

def move_task_to_dev(task_id):
    """Move a specific task to the Dev column"""
    with open(KANBAN_FILE) as f:
        data = json.load(f)

    moved = False
    for col in data["columns"]:
        if col["id"] == "dev":
            for task in col["tasks"]:
                if task.get("id") == task_id:
                    # Check if already in dev
                    print(f"  ⚠️ Task {task_id} already in Dev column")
                    return False

    # Find task in current column
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("id") == task_id:
                # Move to dev
                task["column"] = "dev"
                task["done"] = False
                col["tasks"].remove(task)
                data["columns"][3]["tasks"].append(task)
                moved = True
                print(f"  ✅ Moved task {task_id} to Dev column")
                break
        if moved:
            break

    with open(KANBAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return moved

def update_task_status(task_id, progress_pct, status_message):
    """Update task progress and status"""
    with open(KANBAN_FILE) as f:
        data = json.load(f)

    updated = False
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("id") == task_id:
                task["progress"] = progress_pct
                task["status"] = status_message
                task["updatedAt"] = "2026-04-19T23:11:00Z"
                print(f"  📊 Task {task_id}: {progress_pct}% complete - {status_message}")
                updated = True
                break
        if updated:
            break

    with open(KANBAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return updated

def generate_progress_update():
    """Generate progress update for all dev column tasks"""
    with open(KANBAN_FILE) as f:
        data = json.load(f)

    dev_tasks = [t for col in data["columns"] if col["id"] == "dev" for t in col["tasks"]]

    if not dev_tasks:
        return None

    message = "**🔄 Development Progress Update**\n\n"

    for task in dev_tasks:
        status = task.get("status", "In Progress")
        progress = task.get("progress", 0)
        message += f"**{task['text']}**\n"
        message += f"   📈 {progress}% complete\n"
        message += f"   {status}\n\n"

    return message

def main():
    print("🔄 Phase 4: Auto-Queue and Workflow Automation\n")

    # Demo: Move the "April 20 Kanban Board MVP" task to Dev
    print("Moving 'April 20 Kanban Board MVP' to Dev column...")
    moved = move_task_to_dev(5)  # This would be the actual task ID

    if moved:
        print("\nTask moved to Dev. Starting development work...")
        update_task_status(5, 10, "Code structure established - MVP skeleton complete")

    # Generate progress update
    progress_update = generate_progress_update()
    if progress_update:
        print("\nProgress update generated for Telegram")
        print(progress_update)

    print("\n✅ Phase 4: Auto-queue complete")

if __name__ == "__main__":
    main()
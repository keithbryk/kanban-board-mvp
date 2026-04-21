#!/usr/bin/env python3
"""
Enhanced Kanban API with Pipeline Support
Phase 1: Timestamps, activity logging, status tracking
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")

def load_kanban() -> Dict:
    with open(KANBAN_FILE) as f:
        return json.load(f)

def save_kanban(data: Dict):
    with open(KANBAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_task(data: Dict, task_id: int) -> Optional[Dict]:
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("id") == task_id:
                return task
    return None

def get_task_column(data: Dict, task_id: int) -> Optional[str]:
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("id") == task_id:
                return col["id"]
    return None

def move_task(task_id: int, to_column: str, reason: str = "") -> Dict:
    """Move a task to a different column with full activity logging"""
    data = load_kanban()
    
    # Validate target column
    valid_columns = {col["id"]: col for col in data["columns"]}
    if to_column not in valid_columns:
        return {"success": False, "error": f"Invalid column: {to_column}"}
    
    # Find task
    task = None
    from_column = None
    for col in data["columns"]:
        for t in col["tasks"]:
            if t.get("id") == task_id:
                task = t
                from_column = col["id"]
                break
    
    if not task:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    if from_column == to_column:
        return {"success": False, "error": f"Task already in {to_column}"}
    
    # Remove from current column
    for col in data["columns"]:
        if col["id"] == from_column:
            col["tasks"] = [t for t in col["tasks"] if t.get("id") != task_id]
            break
    
    # Update task
    task["column"] = to_column
    task["movedAt"] = now_iso()
    
    # Update column-specific timestamp
    if to_column == "dev":
        task["movedToDevAt"] = now_iso()
    elif to_column == "review":
        task["movedToReviewAt"] = now_iso()
    elif to_column == "done":
        task["completedAt"] = now_iso()
        task["done"] = True
    
    # Log activity
    if "activity" not in task:
        task["activity"] = []
    
    task["activity"].append({
        "timestamp": now_iso(),
        "action": "moved",
        "from": from_column,
        "to": to_column,
        "reason": reason
    })
    
    # Add to target column
    valid_columns[to_column]["tasks"].append(task)
    
    save_kanban(data)
    
    return {
        "success": True,
        "task_id": task_id,
        "from": from_column,
        "to": to_column,
        "activity": task["activity"]
    }

def add_task(text: str, column: str = "ideation", notes: str = "", priority: str = "medium") -> Dict:
    """Add a new task with full timestamps"""
    data = load_kanban()
    
    # Find max task ID
    max_id = 0
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("id", 0) > max_id:
                max_id = task.get("id", 0)
    
    new_id = max_id + 1
    timestamp = now_iso()
    
    new_task = {
        "id": new_id,
        "text": text,
        "column": column,
        "done": False,
        "notes": notes,
        "priority": priority,
        "createdAt": timestamp,
        f"movedTo{column.capitalize()}At": timestamp,
        "activity": [
            {
                "timestamp": timestamp,
                "action": "created",
                "from": None,
                "to": column
            }
        ]
    }
    
    # Add to appropriate column
    for col in data["columns"]:
        if col["id"] == column:
            col["tasks"].append(new_task)
            break
    
    save_kanban(data)
    
    return {
        "success": True,
        "task_id": new_id,
        "task": new_task
    }

def update_task_notes(task_id: int, notes: str) -> Dict:
    """Update task notes with activity logging"""
    data = load_kanban()
    task = get_task(data, task_id)
    
    if not task:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    old_notes = task.get("notes", "")
    task["notes"] = notes
    task["notesUpdatedAt"] = now_iso()
    
    if "activity" not in task:
        task["activity"] = []
    
    task["activity"].append({
        "timestamp": now_iso(),
        "action": "notes_updated",
        "from": old_notes[:50] + "..." if len(old_notes) > 50 else old_notes,
        "to": notes[:50] + "..." if len(notes) > 50 else notes
    })
    
    save_kanban(data)
    
    return {"success": True, "task": task}

def get_task_history(task_id: int) -> Dict:
    """Get full activity history for a task"""
    data = load_kanban()
    task = get_task(data, task_id)
    
    if not task:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    return {
        "success": True,
        "task_id": task_id,
        "task_text": task.get("text"),
        "current_column": task.get("column"),
        "createdAt": task.get("createdAt"),
        "completedAt": task.get("completedAt"),
        "activity": task.get("activity", [])
    }

def get_pipeline_stats() -> Dict:
    """Get pipeline statistics"""
    data = load_kanban()
    
    stats = {
        "total_tasks": 0,
        "by_column": {},
        "by_status": {"active": 0, "completed": 0, "blocked": 0},
        "recent_activity": []
    }
    
    for col in data["columns"]:
        stats["by_column"][col["id"]] = len(col["tasks"])
        stats["total_tasks"] += len(col["tasks"])
        
        for task in col["tasks"]:
            if task.get("done"):
                stats["by_status"]["completed"] += 1
            else:
                stats["by_status"]["active"] += 1
            
            # Collect recent activity
            for entry in task.get("activity", [])[-3:]:
                entry["task_id"] = task.get("id")
                entry["task_text"] = task.get("text")
                stats["recent_activity"].append(entry)
    
    # Sort recent activity by timestamp
    stats["recent_activity"].sort(key=lambda x: x["timestamp"], reverse=True)
    stats["recent_activity"] = stats["recent_activity"][:10]
    
    return stats

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: kanban-api.py <command> [args]")
        print("Commands: add, move, notes, history, stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "stats":
        import pprint
        pprint.pprint(get_pipeline_stats())
    elif cmd == "add" and len(sys.argv) >= 3:
        result = add_task(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "ideation")
        print(json.dumps(result, indent=2))
    elif cmd == "move" and len(sys.argv) >= 4:
        result = move_task(int(sys.argv[2]), sys.argv[3])
        print(json.dumps(result, indent=2))
    else:
        print("Unknown command or missing arguments")
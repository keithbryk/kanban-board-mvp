#!/usr/bin/env python3
"""
Raz Commands Parser for Kanban
Phase 2: Parse and execute commands from task notes

Commands format: !command: value
Supported commands:
  !move: <column>     - Move task to column (dev, review, done, ideation, definition)
  !priority: <level>  - Set priority (low, medium, high, critical)
  !block: <reason>    - Mark task as blocked with reason
  !done               - Mark task as completed
  !delete             - Delete task entirely
  !assign: <person>   - Assign task to person
  !estimate: <hours>  - Set time estimate in hours
  !watch              - Add to Raz's watch list for active monitoring
"""

import re
from typing import Dict, List
from pathlib import Path
import json

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")

VALID_COLUMNS = ["ideation", "definition", "dev", "review", "done"]
VALID_PRIORITIES = ["low", "medium", "high", "critical"]

COMMAND_PATTERNS = {
    "move": re.compile(r'!move:\s*(\w+)', re.IGNORECASE),
    "priority": re.compile(r'!priority:\s*(\w+)', re.IGNORECASE),
    "block": re.compile(r'!block:\s*(.+)', re.IGNORECASE),
    "done": re.compile(r'!done\b', re.IGNORECASE),
    "delete": re.compile(r'!delete\b', re.IGNORECASE),
    "assign": re.compile(r'!assign:\s*(.+)', re.IGNORECASE),
    "estimate": re.compile(r'!estimate:\s*(\d+(?:\.\d+)?)\s*(h|hours?)?', re.IGNORECASE),
    "watch": re.compile(r'!watch\b', re.IGNORECASE),
}

def now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def parse_commands_from_notes(notes: str) -> List[Dict]:
    commands = []
    for cmd_name, pattern in COMMAND_PATTERNS.items():
        matches = pattern.finditer(notes)
        for match in matches:
            if cmd_name in ["done", "delete", "watch"]:
                commands.append({"command": cmd_name, "value": None, "raw": match.group(0)})
            else:
                commands.append({"command": cmd_name, "value": match.group(1).strip() if match.lastindex else None, "raw": match.group(0)})
    return commands

def process_all_commands() -> Dict:
    with open(KANBAN_FILE) as f:
        data = json.load(f)
    
    results = {
        "tasks_processed": 0,
        "commands_executed": 0,
        "errors": [],
        "actions": []
    }
    
    tasks_to_delete = []
    tasks_to_move = []
    
    for col in data["columns"]:
        for task in col["tasks"]:
            notes = task.get("notes", "")
            if "!" not in notes:
                continue
            
            commands = parse_commands_from_notes(notes)
            if not commands:
                continue
            
            results["tasks_processed"] += 1
            from_column = col["id"]
            
            for cmd in commands:
                result = execute_command(task, cmd["command"], cmd["value"], from_column, data)
                if result.get("success"):
                    results["commands_executed"] += 1
                    results["actions"].append({
                        "task_id": task.get("id"),
                        "task_text": task.get("text")[:50],
                        "command": cmd["raw"],
                        "result": result
                    })
                    
                    if cmd["command"] == "delete":
                        tasks_to_delete.append(task.get("id"))
                    elif cmd["command"] == "move":
                        tasks_to_move.append({
                            "task": task,
                            "from_col": from_column,
                            "to_col": result.get("to")
                        })
                else:
                    results["errors"].append({
                        "task_id": task.get("id"),
                        "command": cmd["raw"],
                        "error": result.get("error")
                    })
            
            # Clean up notes
            new_notes = notes
            for cmd in commands:
                new_notes = new_notes.replace(cmd["raw"], "").strip()
            new_notes = re.sub(r'\s+', ' ', new_notes).strip()
            task["notes"] = new_notes if new_notes else ""
    
    # Execute moves (after processing all commands to avoid conflicts)
    for move_info in tasks_to_move:
        task = move_info["task"]
        from_col_id = move_info["from_col"]
        to_col_id = move_info["to_col"]
        
        # Remove from source column
        for col in data["columns"]:
            if col["id"] == from_col_id:
                col["tasks"] = [t for t in col["tasks"] if t.get("id") != task.get("id")]
                break
        
        # Add to target column
        for col in data["columns"]:
            if col["id"] == to_col_id:
                col["tasks"].append(task)
                break
    
    # Delete tasks
    for task_id in tasks_to_delete:
        for col in data["columns"]:
            col["tasks"] = [t for t in col["tasks"] if t.get("id") != task_id]
    
    with open(KANBAN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return results

def execute_command(task: Dict, command: str, value, from_column: str, data: Dict) -> Dict:
    if command == "move":
        target_column = value.lower().strip()
        if target_column not in VALID_COLUMNS:
            return {"success": False, "error": f"Invalid column: {target_column}"}
        if target_column == from_column:
            return {"success": True, "action": "already_in_column", "to": target_column}
        
        task["column"] = target_column
        task["movedAt"] = now_iso()
        if target_column == "dev":
            task["movedToDevAt"] = now_iso()
        elif target_column == "review":
            task["movedToReviewAt"] = now_iso()
        elif target_column == "done":
            task["completedAt"] = now_iso()
            task["done"] = True
        
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "from": from_column,
            "to": target_column,
            "command": f"!move: {target_column}"
        })
        return {"success": True, "action": "moved", "to": target_column}
    
    elif command == "priority":
        priority = value.lower().strip()
        if priority not in VALID_PRIORITIES:
            return {"success": False, "error": f"Invalid priority: {priority}"}
        task["priority"] = priority
        task["prioritySetAt"] = now_iso()
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "command": f"!priority: {priority}"
        })
        return {"success": True, "action": "priority_set", "priority": priority}
    
    elif command == "block":
        task["blocked"] = True
        task["blockReason"] = value.strip()
        task["blockedAt"] = now_iso()
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "command": f"!block: {value.strip()}"
        })
        return {"success": True, "action": "blocked", "reason": value.strip()}
    
    elif command == "done":
        task["done"] = True
        task["column"] = "done"
        task["completedAt"] = now_iso()
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "from": from_column,
            "to": "done",
            "command": "!done"
        })
        return {"success": True, "action": "completed"}
    
    elif command == "delete":
        return {"success": True, "action": "deleted"}
    
    elif command == "assign":
        task["assignedTo"] = value.strip()
        task["assignedAt"] = now_iso()
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "command": f"!assign: {value.strip()}"
        })
        return {"success": True, "action": "assigned", "to": value.strip()}
    
    elif command == "estimate":
        try:
            hours = float(re.match(r'(\d+(?:\.\d+)?)', value).group(1))
            task["estimatedHours"] = hours
            task["estimatedAt"] = now_iso()
            if "activity" not in task:
                task["activity"] = []
            task["activity"].append({
                "timestamp": now_iso(),
                "action": "raz_command",
                "command": f"!estimate: {hours}h"
            })
            return {"success": True, "action": "estimated", "hours": hours}
        except:
            return {"success": False, "error": "Invalid estimate format"}
    
    elif command == "watch":
        task["watchedByRaz"] = True
        task["watchedAt"] = now_iso()
        return {"success": True, "action": "watched"}
    
    return {"success": False, "error": f"Unknown command: {command}"}

def get_watched_tasks() -> List[Dict]:
    with open(KANBAN_FILE) as f:
        data = json.load(f)
    watched = []
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("watchedByRaz"):
                watched.append({
                    "id": task.get("id"),
                    "text": task.get("text"),
                    "column": col["title"],
                    "watchedAt": task.get("watchedAt")
                })
    return watched

def get_blocked_tasks() -> List[Dict]:
    with open(KANBAN_FILE) as f:
        data = json.load(f)
    blocked = []
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("blocked"):
                blocked.append({
                    "id": task.get("id"),
                    "text": task.get("text"),
                    "column": col["title"],
                    "reason": task.get("blockReason"),
                    "blockedAt": task.get("blockedAt")
                })
    return blocked

if __name__ == "__main__":
    import sys
    import pprint
    
    if len(sys.argv) < 2:
        print("Usage: raz-commands.py [process|watched|blocked]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "process":
        print("🔄 Processing Raz commands...")
        result = process_all_commands()
        print(f"\n📊 Results:")
        print(f"  Tasks processed: {result['tasks_processed']}")
        print(f"  Commands executed: {result['commands_executed']}")
        if result['actions']:
            print("\n✅ Actions taken:")
            for action in result['actions']:
                print(f"  - Task {action['task_id']}: {action['result'].get('action')}")
        if result['errors']:
            print("\n❌ Errors:")
            for err in result['errors']:
                print(f"  - Task {err['task_id']}: {err['error']}")
    elif cmd == "watched":
        watched = get_watched_tasks()
        print(f"👀 Raz is watching {len(watched)} task(s)")
        for t in watched:
            print(f"  - [{t['column']}] {t['text'][:50]}")
    elif cmd == "blocked":
        blocked = get_blocked_tasks()
        print(f"🚧 {len(blocked)} task(s) blocked")
        for t in blocked:
            print(f"  - [{t['column']}] {t['text'][:50]} - {t['reason']}")
    else:
        print(f"Unknown command: {cmd}")
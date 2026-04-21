#!/usr/bin/env python3
"""
Complete Hourly Review: Extraction → AI Verification → Auto-Queue
Full pipeline from notes to task execution + Raz Commands
"""
import os
os.environ["PATH"] = "/home/kbryk/.npm-global/bin:/usr/local/bin:/usr/bin:/bin" + os.pathsep + os.environ.get("PATH", "")

import json
import re
from pathlib import Path
import subprocess
import requests
import urllib.parse

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")
TELEGRAM_BOT_TOKEN = "8711413674:AAHKhsk6LPKMz8NR9VNN5w3zPSlkgwUyalg"
TELEGRAM_CHAT_ID = "8284629061"

TASK_PATTERNS = [
    r'assign(?:ing|ed)?\s+to\s+\w+\s+(to\s+)?([^\.\n]{5,60})',
    r'complete(?:d)?\s+implementation:?\s+([^\.\n]{5,80})',
    r'complete(?:d)?\s+(?:setup|build|creation)\s+(?:of\s+)?([^\.\n]{5,60})',
    r'(?:^|\s)(implement|build|create|develop|configure|setup|enable|add|integrate|fix|deploy|test|analyze|review)\s+([^\.\n]{5,70})',
    r'need(?:s)?\s+to\s+([^\.\n]{5,60})',
    r'(?:^|\s)(must|should|will|can)\s+([^\.\n]{5,60})',
]

# Raz Commands patterns
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

VALID_COLUMNS = ["ideation", "definition", "dev", "review", "done"]

def now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def extract_tasks_from_text(text):
    tasks = []
    seen = set()
    for pattern in TASK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            task_text = match.group(match.lastindex).strip() if match.lastindex else match.group(1).strip()
            if len(task_text) < 8:
                continue
            skip_words = ['the', 'this', 'that', 'these', 'those', 'something', 'it', 'things', 'stuff']
            if task_text.lower() in skip_words or task_text.lower().startswith(tuple(skip_words)):
                continue
            if task_text not in seen:
                seen.add(task_text)
                tasks.append(task_text)
    return tasks

def parse_commands_from_notes(notes: str) -> list:
    """Extract all Raz commands from task notes"""
    commands = []
    for cmd_name, pattern in COMMAND_PATTERNS.items():
        matches = pattern.finditer(notes)
        for match in matches:
            if cmd_name in ["done", "delete", "watch"]:
                commands.append({"command": cmd_name, "value": None, "raw": match.group(0)})
            else:
                commands.append({"command": cmd_name, "value": match.group(1).strip() if match.lastindex else None, "raw": match.group(0)})
    return commands

def execute_raz_command(task: dict, command: str, value, from_column: str) -> dict:
    """Execute a single Raz command on a task"""
    if command == "move":
        target = value.lower().strip()
        if target not in VALID_COLUMNS:
            return {"success": False, "error": f"Invalid column: {target}"}
        task["column"] = target
        task["movedAt"] = now_iso()
        if target == "dev":
            task["movedToDevAt"] = now_iso()
        elif target == "review":
            task["movedToReviewAt"] = now_iso()
        elif target == "done":
            task["completedAt"] = now_iso()
            task["done"] = True
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "from": from_column,
            "to": target,
            "command": f"!move: {target}"
        })
        return {"success": True, "action": "moved", "to": target}
    
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
    
    elif command == "priority":
        task["priority"] = value.lower().strip()
        task["prioritySetAt"] = now_iso()
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "command": f"!priority: {value}"
        })
        return {"success": True, "action": "priority_set", "priority": value}
    
    elif command == "block":
        task["blocked"] = True
        task["blockReason"] = value.strip()
        task["blockedAt"] = now_iso()
        if "activity" not in task:
            task["activity"] = []
        task["activity"].append({
            "timestamp": now_iso(),
            "action": "raz_command",
            "command": f"!block: {value}"
        })
        return {"success": True, "action": "blocked", "reason": value}
    
    elif command == "watch":
        task["watchedByRaz"] = True
        task["watchedAt"] = now_iso()
        return {"success": True, "action": "watched"}
    
    return {"success": False, "error": f"Unknown command: {command}"}

def get_ai_response(prompt):
    try:
        auth_path = Path("/home/kbryk/.openclaw/agents/main/agent/auth-profiles.json")
        if auth_path.exists():
            with open(auth_path) as f:
                auth = json.load(f)
            api_key = auth.get("profiles", {}).get("openrouter:default", {}).get("key", "")
        
        if not api_key:
            return None
            
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "minimax/minimax-m2.5:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    return None

def analyze_task(task_text, context=""):
    prompt = f"""Analyze this task and return JSON:
Task: {task_text}
Context: {context}
Return ONLY valid JSON like: {{"verdict": "execute", "estimated_time_minutes": 15}}"""
    
    response = get_ai_response(prompt)
    if response:
        try:
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    return {"verdict": "review", "estimated_time_minutes": 15}

def main():
    with open(KANBAN_FILE) as f:
        data = json.load(f)

    all_notes = []
    extracted_tasks = []
    raz_commands_executed = []
    tasks_to_delete = []

    # Phase 1: Extract tasks from notes
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("notes") and task.get("notes", "").strip():
                all_notes.append({
                    "column": col["title"],
                    "task_text": task["text"],
                    "notes": task["notes"],
                    "task_id": task.get("id")
                })
                extracted_tasks.extend(extract_tasks_from_text(task["notes"]))
                
                # Phase 2: Process Raz commands
                commands = parse_commands_from_notes(task["notes"])
                for cmd in commands:
                    result = execute_raz_command(task, cmd["command"], cmd["value"], col["id"])
                    if result.get("success"):
                        raz_commands_executed.append({
                            "task_id": task.get("id"),
                            "task_text": task.get("text")[:40],
                            "command": cmd["raw"],
                            "result": result
                        })
                        if cmd["command"] == "delete":
                            tasks_to_delete.append(task.get("id"))
                    # Clean command from notes
                    task["notes"] = task["notes"].replace(cmd["raw"], "").strip()

    if not extracted_tasks and not raz_commands_executed:
        print("No tasks or commands found")
        return

    print(f"📝 Found {len(extracted_tasks)} tasks, {len(raz_commands_executed)} Raz commands")

    approved = []
    need_review = []

    for task_text in extracted_tasks:
        analysis = analyze_task(task_text, "Kanban Board MVP")
        if analysis.get("verdict") == "execute":
            approved.append(task_text)
        else:
            need_review.append(task_text)
        print(f"  Task: {task_text[:50]}... -> {analysis.get('verdict')}")

    # Delete marked tasks
    for task_id in tasks_to_delete:
        for col in data["columns"]:
            col["tasks"] = [t for t in col["tasks"] if t.get("id") != task_id]

    # Move approved tasks to Dev
    print(f"🔄 Auto-queue")
    for task_text in approved:
        for col in data["columns"]:
            for t in col["tasks"]:
                if t["text"] == task_text and t["column"] not in ["dev", "review", "done"]:
                    print(f"  🚀 Moving '{task_text[:40]}...' to Dev...")
                    t["column"] = "dev"
                    t["movedToDevAt"] = now_iso()
                    if "activity" not in t:
                        t["activity"] = []
                    t["activity"].append({
                        "timestamp": now_iso(),
                        "action": "auto_queue",
                        "from": t["column"],
                        "to": "dev"
                    })
                    break

    with open(KANBAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # Build report
    message = "**📋 Kanban Hourly Review**\n\n"
    
    if raz_commands_executed:
        message += f"⚡ **Raz Commands Executed: {len(raz_commands_executed)}**\n"
        for cmd in raz_commands_executed[:3]:
            message += f"  • `{cmd['command']}` on Task {cmd['task_id']}\n"
        message += "\n"
    
    if all_notes:
        message += f"📝 {len(all_notes)} task(s) with notes:\n\n"
        for note in all_notes[:2]:
            message += f"• {note['task_text']}\n"
    
    message += f"\n**✅ Approved: {len(approved)} | Need Review: {len(need_review)}**\n"

    encoded_message = urllib.parse.quote(message)
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        "-d", f"chat_id={TELEGRAM_CHAT_ID}&text={encoded_message}&parse_mode=Markdown"
    ], capture_output=True, check=False)

    print(f"\n✅ Done: {len(approved)} approved, {len(need_review)} need review, {len(raz_commands_executed)} raz commands")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Hourly Kanban Review with AI Verification and Task Execution
"""
import json
import re
from pathlib import Path
import subprocess
import os

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")
TELEGRAM_BOT_TOKEN = "8711413674:AAHKhsk6LPKMz8NR9VNN5w3zPSlkgwUyalg"
TELEGRAM_CHAT_ID = "8284629061"

TASK_PATTERNS = [
    r'(?:\*\*)?do\s+(?:this|that|it|the)?\s+(.*?)(?:\,|\.|\n|$)',
    r'(?:\*\*)?(?:create|develop|build|implement|setup|configure|review|analyze|deploy|test)\s+(.*?)(?:\,|\.|\n|$)',
]

def extract_tasks_from_text(text):
    """Extract potential tasks from text"""
    tasks = []
    seen = set()

    for pattern in TASK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            task_text = match.group(1).strip()
            if len(task_text) < 5 or any(x in task_text.lower() for x in ['notes', 'see', 'note']):
                continue
            if task_text not in seen:
                seen.add(task_text)
                tasks.append({
                    "text": task_text,
                    "confidence": 0.75
                })

    return tasks

def get_ai_response(prompt):
    """Send prompt to AI"""
    try:
        result = subprocess.run([
            "openclaw", "infer", "execute", "openrouter/minimax/minimax-m2.5:free", "--prompt", prompt
        ], capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"AI failed: {e}")
        return None

def analyze_task(task_text, context=""):
    """Analyze task feasibility"""
    prompt = f"""Analyze: {task_text}
Context: {context}

Verdict (execute|review|block):
1. feasibility (High/Medium/Low)
2. complexity (Simple/Medium/Complex)
3. estimated_time_minutes (number)
4. suggestions (3 bullet points)

Respond as JSON: {{"verdict": "...", "feasibility": "...", "complexity": "...", "estimated_time_minutes": ...}}"""

    response = get_ai_response(prompt)
    if response:
        try:
            return json.loads(response)
        except:
            return {
                "verdict": "review",
                "feasibility": "Medium",
                "complexity": "Medium",
                "estimated_time_minutes": 15
            }

    return {
        "verdict": "review",
        "feasibility": "Medium",
        "complexity": "Medium",
        "estimated_time_minutes": 15
    }

def main():
    # Load kanban data
    with open(KANBAN_FILE) as f:
        data = json.load(f)

    all_notes = []
    extracted_tasks = []

    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("notes") and task.get("notes", "").strip():
                all_notes.append({
                    "column": col["title"],
                    "task_text": task["text"],
                    "notes": task["notes"],
                    "task_id": task.get("id")
                })
                for t in extract_tasks_from_text(task["notes"]):
                    extracted_tasks.append({
                        "provenance": task["text"],
                        "task": t["text"],
                        "confidence": t["confidence"],
                        "parent_id": task.get("id")
                    })

    if not extracted_tasks:
        return

    # Verify and analyze all tasks
    verified = []
    for task in extracted_tasks:
        analysis = analyze_task(task['task'], task['provenance'])
        verified.append({**task, **analysis})

    # Count approvals
    approved = [t for t in verified if t['verdict'] == 'execute']
    need_review = [t for t in verified if t['verdict'] == 'review']

    # Build message
    message = "**📋 Kanban Hourly Review**\n\n"

    if all_notes:
        message += f"{len(all_notes)} task(s) with notes:\n\n"
        for note in all_notes[:3]:  # First 3 notes
            message += f"**{note['column']}** - {note['task_text']}\n"
            message += note['notes'][:150] + "...\n\n"

    message += f"**🔍 AI Verified {len(verified)} task(s)**\n\n"

    if approved:
        message += f"**✅ APPROVED TO EXECUTE ({len(approved)})**\n\n"
        for t in approved[:3]:
            message += f"• {t['task']} (~{t.get('estimated_time_minutes', 15)}m)\n"

    if need_review:
        message += f"**👁️ NEEDS REVIEW ({len(need_review)})**\n\n"
        for t in need_review[:3]:
            message += f"• {t['task']}\n"

    message += "\nI'm reviewing and will execute approved tasks."

    # Send to Telegram
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        "-d", f'{{"chat_id": "{TELEGRAM_CHAT_ID}", "text": "{message}"}}'
    ], capture_output=True, check=False)

    print(f"Hourly review complete: {len(approved)} approved, {len(need_review)} need review")

if __name__ == "__main__":
    main()
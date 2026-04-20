#!/usr/bin/env python3
"""
Hourly Kanban Review with AI Task Extraction
Extracts tasks from notes and queues them for execution
"""
import json
import re
from pathlib import Path
import subprocess
import os

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")
TELEGRAM_BOT_TOKEN = "8711413674:AAHKhsk6LPKMz8NR9VNN5w3zPSlkgwUyalg"
TELEGRAM_CHAT_ID = "8284629061"

# Regex patterns for task extraction
TASK_PATTERNS = [
    r'(?:\*\*)?do\s+(?:this|that|it|the)?\s+(.*?)(?:\,|\.|\n|$)',
    r'(?:\*\*)?(?:create|develop|build|implement|setup|configure|review|analyze|deploy|test)\s+(.*?)(?:\,|\.|\n|$)',
    r'(?:\*\*)?(?:action|task|item):\s+(.*?)(?:\,|\.|\n|$)',
    r'(?:\*\*)?(?:-\s+)(.*?)(?:\n|$)',
]

def extract_tasks_from_text(text):
    """Extract potential tasks from text using multiple patterns"""
    tasks = []
    seen = set()

    for pattern in TASK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            task_text = match.group(1).strip()
            # Filter out noise
            if len(task_text) < 5 or any(x in task_text.lower() for x in ['notes', 'see', 'note']):
                continue
            if task_text not in seen:
                seen.add(task_text)
                tasks.append({
                    "text": task_text,
                    "confidence": 0.75,  # Base confidence
                    "pattern": pattern[:50] + "..."
                })

    return tasks

def process_kanban_notes():
    """Process all Kanban notes and extract tasks"""
    with open(KANBAN_FILE) as f:
        data = json.load(f)

    all_notes = []
    for col in data["columns"]:
        for task in col["tasks"]:
            if task.get("notes") and task.get("notes", "").strip():
                all_notes.append({
                    "column": col["title"],
                    "task_text": task["text"],
                    "notes": task["notes"],
                    "task_id": task.get("id")
                })

    extracted_tasks = []
    for note in all_notes:
        tasks = extract_tasks_from_text(note["notes"])
        for task in tasks:
            extracted_tasks.append({
                "provenance": note["task_text"],
                "task": task["text"],
                "confidence": task["confidence"],
                "parent_id": note["task_id"]
            })

    return all_notes, extracted_tasks

def send_to_telegram(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    subprocess.run(["curl", "-s", "-X", "POST", url, "-d", json.dumps(payload)],
                   capture_output=True, check=False)

if __name__ == "__main__":
    all_notes, extracted_tasks = process_kanban_notes()

    if not all_notes and not extracted_tasks:
        print("No notes found - nothing to review")
        exit(0)

    # Build message
    message = "**📋 Kanban Hourly Review**\n\n"

    if all_notes:
        message += f"Found {len(all_notes)} task(s) with notes:\n\n"
        for note in all_notes:
            message += f"**{note['column']}** - {note['task_text']}\n"
            message += note['notes'][:200] + "...\n\n"

    if extracted_tasks:
        message += f"**🔧 AI-Extracted {len(extracted_tasks)} Task(s)**\n\n"
        for task in extracted_tasks:
            confidence = task["confidence"] * 100
            message += f"✅ `{task['task']}` (conf: {confidence:.0f}%)\n"
            message += f"   ↳ From: {task['provenance']}\n\n"

    message += "I will review and perform these tasks."
    send_to_telegram(message)

    print("Review complete - sent to Telegram")
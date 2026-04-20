#!/usr/bin/env python3
"""
Complete Hourly Review: Extraction → AI Verification → Auto-Queue
Full pipeline from notes to task execution
"""
import json
import re
from pathlib import Path
import subprocess

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
                tasks.append(task_text)
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

Verdict: execute|review|block

Return JSON: {{"verdict": "...", "estimated_time_minutes": <num>}}"""
    response = get_ai_response(prompt)
    if response:
        try:
            return json.loads(response)
        except:
            return {"verdict": "review", "estimated_time_minutes": 15}
    return {"verdict": "review", "estimated_time_minutes": 15}

def main():
    # Load data
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
                extracted_tasks.extend(extract_tasks_from_text(task["notes"]))

    if not extracted_tasks:
        print("No tasks extracted")
        return

    # Analyze and approve
    approved = []
    need_review = []

    for task_text in extracted_tasks:
        analysis = analyze_task(task_text, "Kanban Board MVP")
        if analysis.get("verdict") == "execute":
            approved.append(task_text)
        else:
            need_review.append(task_text)

    # Move approved tasks to Dev (simulation)
    print(f"🔄 Phase 4: Auto-queue")
    for task in approved:
        # Find task in ideation or definition columns
        task_found = False
        for col in data["columns"]:
            for t in col["tasks"]:
                if t["text"] == task:
                    print(f"  🚀 Moving '{task}' to Dev...")
                    t["column"] = "dev"
                    task_found = True
                    break
            if task_found:
                break

    with open(KANBAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # Build report
    message = "**📋 Kanban Hourly Review (Phase 4 Complete)**\n\n"

    if all_notes:
        message += f"📝 {len(all_notes)} task(s) with notes:\n\n"
        for note in all_notes[:2]:
            message += f"• {note['task_text']}\n"

    message += f"\n**✅ AI Approved {len(approved)} Task(s)**\n\n"
    for task in approved[:2]:
        message += f"• `{task}`\n"

    if need_review:
        message += f"\n**👁️ Need Review ({len(need_review)}):**\n"
        for task in need_review[:2]:
            message += f"• `{task}`\n"

    # Send to Telegram
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        "-d", f'{{"chat_id": "{TELEGRAM_CHAT_ID}", "text": "{message}"}}'
    ], capture_output=True, check=False)

    print(f"\n✅ Complete: {len(approved)} approved, {len(need_review)} need review")

if __name__ == "__main__":
    main()
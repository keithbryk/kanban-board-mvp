#!/usr/bin/env python3
"""
AI-Powered Task Verification for Kanban Board
Uses AI to analyze extracted tasks and verify feasibility
"""
import json
import subprocess
from pathlib import Path

KANBAN_FILE = Path("/home/kbryk/kanban/kanban.json")
TELEGRAM_BOT_TOKEN = "8711413674:AAHKhsk6LPKMz8NR9VNN5w3zPSlkgwUyalg"
TELEGRAM_CHAT_ID = "8284629061"

# Possible AI models - try in order
AI_MODELS = [
    "openrouter/minimax/minimax-m2.5:free",  # Free option
    "openrouter/z-ai/glm-4.7-flash",        # Fast free option
    "openrouter/minimax/minimax-m2.7",       # Better quality
]

def get_ai_response(prompt, model):
    """Send prompt to AI and get response"""
    try:
        result = subprocess.run([
            "openclaw", "infer", "execute", model, "--prompt", prompt
        ], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"AI call failed: {e}")
        return None

def analyze_task_feasibility(task_text, context=""):
    """Analyze a task for feasibility using AI"""
    prompt = f"""Analyze the following task and determine:

1. Feasibility: Is this task doable? (High/Medium/Low)
2. Complexity: Simple/Medium/Complex
3. Estimated time: How long would it take to complete?
4. Suggestions: What specific steps should be taken?
5. Blocked by: Any dependencies or blockers?

TASK: {task_text}
{f"CONTEXT: {context}" if context else ""}

Respond in JSON format:
{{
  "feasibility": "High|Medium|Low",
  "complexity": "Simple|Medium|Complex",
  "estimated_time_minutes": <number>,
  "suggestions": ["step 1", "step 2", ...],
  "blocked_by": ["dependency1", "dependency2", ...] or [],
  "verdict": "execute|review|block"
}}"""

    for model in AI_MODELS:
        response = get_ai_response(prompt, model)
        if response:
            try:
                # Parse JSON response
                analysis = json.loads(response)
                return {
                    "task": task_text,
                    "feasibility": analysis.get("feasibility", "Medium"),
                    "complexity": analysis.get("complexity", "Medium"),
                    "estimated_time_minutes": analysis.get("estimated_time_minutes", 15),
                    "suggestions": analysis.get("suggestions", []),
                    "blocked_by": analysis.get("blocked_by", []),
                    "verdict": analysis.get("verdict", "review"),
                    "model_used": model
                }
            except json.JSONDecodeError:
                continue

    # Fallback if AI fails
    return {
        "task": task_text,
        "feasibility": "Unknown",
        "complexity": "Unknown",
        "estimated_time_minutes": 15,
        "suggestions": ["Review and verify task manually"],
        "blocked_by": [],
        "verdict": "review",
        "model_used": "fallback"
    }

def verify_all_tasks(extracted_tasks):
    """Verify all extracted tasks"""
    verified_tasks = []

    for task in extracted_tasks:
        context = f"Parent task: {task['provenance']}"
        analysis = analyze_task_feasibility(task['task'], context)
        verified_tasks.append({
            **task,
            **analysis
        })

    return verified_tasks

def format_verification_report(verified_tasks):
    """Format the verification report"""
    if not verified_tasks:
        return "**No tasks to verify.**"

    report = "**🔍 AI Task Verification Report**\n\n"

    high_priority = []
    medium_priority = []
    review_only = []

    for task in verified_tasks:
        if task["verdict"] == "execute":
            high_priority.append(task)
        elif task["verdict"] == "review":
            review_only.append(task)
        else:
            medium_priority.append(task)

    if high_priority:
        report += f"**✅ APPROVED TO EXECUTE ({len(high_priority)} task(s))**\n\n"
        for task in high_priority:
            report += f"**{task['task']}**\n"
            report += f"   ⏱️ Time: ~{task['estimated_time_minutes']} mins\n"
            if task['blocked_by']:
                report += f"   ⚠️ Blocked by: {', '.join(task['blocked_by'])}\n"
            report += f"   💡 {task['suggestions'][0] if task['suggestions'] else 'Review and implement'}\n\n"

    if review_only:
        report += f"**👁️ NEEDS REVIEW ({len(review_only)} task(s))**\n\n"
        for task in review_only:
            report += f"**{task['task']}**\n"
            report += f"   ⏱️ Time: ~{task['estimated_time_minutes']} mins\n"
            report += f"   🤔 {task['feasibility']} - {task['complexity']}\n\n"

    if medium_priority:
        report += f"**⏸️ PENDING ({len(medium_priority)} task(s))**\n\n"
        for task in medium_priority:
            report += f"**{task['task']}**\n"
            report += f"   ⚠️ {task['feasibility']} feasibility\n\n"

    return report

def main():
    # Load extracted tasks from kanban
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
                tasks = extract_tasks_from_text(task["notes"])
                for t in tasks:
                    extracted_tasks.append({
                        "provenance": task["text"],
                        "task": t["text"],
                        "confidence": t["confidence"],
                        "parent_id": task.get("id")
                    })

    if not extracted_tasks:
        print("No tasks to verify")
        return

    # Verify all tasks
    verified_tasks = verify_all_tasks(extracted_tasks)

    # Format report
    report = format_verification_report(verified_tasks)

    # Send to Telegram
    send_to_telegram(report)

    print(f"Verified {len(verified_tasks)} task(s)")
    print(f"Approved to execute: {sum(1 for t in verified_tasks if t['verdict'] == 'execute')}")

if __name__ == "__main__":
    main()
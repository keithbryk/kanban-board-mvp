# April 20 Kanban Board MVP

An intelligent, AI-powered Kanban board with automated workflow orchestration.

## ✨ Features

### 🎯 5-Column Workflow Pipeline
- **Ideation** - New ideas and concepts
- **Definition** - Specs and requirements
- **Dev** - Implementation work (auto-queued)
- **Review** - Testing and feedback
- **Done** - Completed tasks

### 🤖 AI-Powered Intelligence
- **Task Extraction** - Automatically finds action items in notes
- **Feasibility Analysis** - AI assesses High/Medium/Low feasibility
- **Time Estimation** - Knows how long tasks will take
- **Approval Logic** - AI says execute|review|block

### 📡 Automation
- **Auto-Queue** - Approved tasks go to Dev column
- **Progress Tracking** - Tasks show 0-100% completion
- **Telegram Updates** - Hourly status reports
- **Cron Integration** - Hourly reviews at :01

### 💅 Professional UI
- Dark theme (GitHub/VS Code style)
- Uniform column widths (280px)
- Markdown rendering in notes
- Search across all content

## 🚀 Quick Start

```bash
# Start the server
cd /home/kbryk/kanban
python3 kanban-api.py

# Or use the start script
./start.sh
```

Access at: http://localhost:8081

## 📝 Using the Board

### Adding Notes
- Click on any task to add/edit notes
- Use markdown for formatting:
  - `**bold text**` → **bold**
  - `*italic text*` → *italic*
  - `- list item` → bullet points

### Task Extraction
- Type actions in notes: "do this", "create X", "- item"
- AI automatically extracts them
- Review verified tasks in hourly report

### Automation
- Hourly cron runs at :01 of every hour
- Approved tasks move to Dev column automatically
- Get Telegram updates with progress

## 🛠️ Tech Stack

- **Runtime:** Python HTTP server
- **Database:** JSON (expandable to SQLite)
- **AI:** OpenRouter MiniMax M2.5 Free
- **Automation:** Cron (hourly)

## 📦 Files

- `kanban.json` - Main database
- `kanban-api.py` - HTTP server API
- `app.js` - Frontend JavaScript
- `index.html` - Main HTML template
- `kanban_server.py` - MCP server
- `review-kanban.sh` - Hourly automation
- `README.md` - This file

## 🔧 Customization

### Change Port
Edit `kanban-api.py` line 60:
```python
server = socketserver.TCPServer(("", 8081), KanbanHandler)
```

### Modify AI Model
Edit `review-kanban.sh` or `review-hourly.py`:
```python
"openrouter/minimax/minimax-m2.5:free"  # Change model
```

### Add New Columns
Edit `kanban.json` structure or `app.js` headerMap.

## 🤝 MCP Integration

The Kanban board includes an MCP server for programmatic access:

```python
# Tools available:
- kanban_get_tasks
- kanban_add_task
- kanban_move_task
- kanban_update_task
- kanban_delete_task
```

## 📊 Current Status

- **Ideation:** 2 tasks
- **Definition:** 1 task
- **Dev:** 0 tasks
- **Review:** 1 task
- **Done:** 2 tasks

## 🔄 Pipeline Progression

```
Notes → Extract → Verify → Approve → Dev → Review → Done
```

## 📄 License

MIT

---

**Built with ❤️ for April 20 MVP**

Transform your Kanban board from simple task tracker → intelligent workflow orchestrator.
let tasks = [];
let taskIdCounter = 1;
let editingTaskId = null;

async function loadData() {
    try {
        const res = await fetch('/api/tasks');
        const data = await res.json();
        tasks = data.tasks || [];
        taskIdCounter = tasks.reduce((max, t) => Math.max(max, t.id || 0), 0) + 1;
        renderBoard();
    } catch (err) {
        console.error('Error loading:', err);
        document.getElementById('board').innerText = 'Error loading data: ' + err.message;
    }
}

async function saveData() {
    try {
        await fetch('/api/tasks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(tasks)
        });
    } catch (err) {
        console.error('Error saving:', err);
    }
}

document.getElementById('addTaskBtn').addEventListener('click', function() {
    const input = document.getElementById('taskInput');
    const text = input.value.trim();
    if (!text) return;

    tasks.push({id: taskIdCounter++, text: text, column: 'ideation', done: false, notes: ''});
    input.value = '';
    saveData();
    renderBoard();
});

function renderBoard() {
    const board = document.getElementById('board');
    const columns = {};

    tasks.forEach(t => {
        if (!columns[t.column]) columns[t.column] = [];
        columns[t.column].push(t);
    });

    board.innerHTML = '';
    Object.keys(columns).forEach(colId => {
        const colDiv = document.createElement('div');
        colDiv.className = 'column';

        const headerMap = {
            'ideation': 'Ideation',
            'definition': 'Definition',
            'dev': 'Dev',
            'review': 'Review',
            'done': 'Done'
        };

        colDiv.innerHTML = `<div class="column-header column-${colId}">${headerMap[colId]}</div>`;

        columns[colId].forEach(task => {
            const taskDiv = document.createElement('div');
            taskDiv.className = 'task';

            const title = document.createElement('div');
            title.className = 'task-title';
            title.innerText = task.text;

            const notesDiv = document.createElement('div');
            notesDiv.className = 'task-notes';
            notesDiv.innerHTML = marked.parse(task.notes || '(No notes)');

            const textArea = document.createElement('textarea');
            textArea.placeholder = 'Add notes... (support for markdown: **bold**, *italic*, - lists)';
            textArea.value = task.notes || '';
            textArea.oninput = function() {
                task.notes = this.value;
                // Live preview update
                notesDiv.innerHTML = marked.parse(this.value || '(No notes)');
            };

            taskDiv.appendChild(title);
            taskDiv.appendChild(notesDiv);
            taskDiv.appendChild(textArea);
            colDiv.appendChild(taskDiv);
        });

        board.appendChild(colDiv);
    });
}

// Simple markdown parser
const marked = {
    parse: function(text) {
        if (!text) return '(No notes)';
        let html = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/-(.*?)$/gm, '<li>$1</li>')
            .replace(/^(\*\*.*?\*\*|.*?)(\n|$)/gm, function(match) {
                return match.startsWith('**') ? '<strong>' + match.replace(/\*\*/g, '') + '</strong>' : match;
            });
        return html.replace(/<li>/g, '<li>').replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>');
    }
};

loadData();
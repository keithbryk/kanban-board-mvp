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

    tasks.push({id: taskIdCounter++, text: text, column: 'todo', done: false, notes: ''});
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
        colDiv.innerHTML = '<h3>' + colId + '</h3>';

        columns[colId].forEach(task => {
            const taskDiv = document.createElement('div');
            taskDiv.className = 'task';

            const header = document.createElement('div');
            header.style.fontWeight = 'bold';
            header.innerText = task.text;

            const notesDiv = document.createElement('div');
            notesDiv.className = 'task-notes';
            notesDiv.innerText = task.notes || '(No notes)';

            const textArea = document.createElement('textarea');
            textArea.placeholder = 'Add notes...';
            textArea.value = task.notes || '';
            textArea.oninput = function() {
                task.notes = this.value;
            };

            taskDiv.appendChild(header);
            taskDiv.appendChild(notesDiv);
            taskDiv.appendChild(textArea);
            colDiv.appendChild(taskDiv);
        });

        board.appendChild(colDiv);
    });
}

loadData();
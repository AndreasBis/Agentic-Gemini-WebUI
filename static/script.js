const socket = io();
const outputArea = document.getElementById('output-area');
const inputContainer = document.getElementById('input-container');
const inputField = document.getElementById('user-input');
const menuOverlay = document.getElementById('menu-overlay');
const statusIndicator = document.getElementById('status-indicator');
const backBtn = document.getElementById('back-btn');
const historyList = document.getElementById('history-list');
const sidebar = document.getElementById('history-sidebar');

let isWaitingForInput = false;
let currentInputPrompt = '>';

// Initial Load
fetchHistory();

// Initialize Markdown
marked.setOptions({
    highlight: function(code, lang) {
        const language = hljs.getLanguage(lang) ? lang : 'plaintext';
        return hljs.highlight(code, { language }).value;
    },
    langPrefix: 'hljs language-'
});

socket.on('connect', () => {
    statusIndicator.textContent = 'Online';
});

socket.on('disconnect', () => {
    statusIndicator.textContent = 'Offline';
});

socket.on('server_output', (msg) => {
    appendMessage(msg.data, 'agent');
});

socket.on('request_input', (data) => {
    isWaitingForInput = true;
    currentInputPrompt = data.prompt || '>';
    inputContainer.classList.remove('hidden');
    statusIndicator.textContent = 'Awaiting Input';
    inputField.focus();
    scrollToBottom();
});

socket.on('session_ended', () => {
    isWaitingForInput = false;
    inputContainer.classList.add('hidden');
    statusIndicator.textContent = 'Finished';
    backBtn.classList.remove('hidden');
    scrollToBottom();
    fetchHistory();
});

function toggleSidebar() {
    sidebar.classList.toggle('collapsed');
}

function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = 'message-container ' + (sender === 'user' ? 'user-message' : 'agent-message');
    
    if (sender === 'agent') {
        div.innerHTML = marked.parse(text);
    } else {
        div.textContent = text;
    }
    
    outputArea.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    outputArea.scrollTop = outputArea.scrollHeight;
}

function selectMode(mode) {
    menuOverlay.classList.remove('active');
    backBtn.classList.add('hidden');
    outputArea.innerHTML = ''; 
    socket.emit('start_mode', { mode: mode });
    statusIndicator.textContent = 'Running Mode ' + mode;
}

function showMenu() {
    menuOverlay.classList.add('active');
    backBtn.classList.add('hidden');
    statusIndicator.textContent = 'Online';
    inputContainer.classList.add('hidden');
}

function sendInput() {
    if (!isWaitingForInput) return;
    
    const text = inputField.value;
    
    appendMessage(currentInputPrompt + ' ' + text, 'user');
    
    socket.emit('user_input', { message: text });
    
    inputField.value = '';
    inputContainer.classList.add('hidden');
    isWaitingForInput = false;
    statusIndicator.textContent = 'Processing...';
}

inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendInput();
    }
});

// History Functions
async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const sessions = await response.json();
        renderHistoryList(sessions);
    } catch (err) {
        console.error('Failed to fetch history:', err);
    }
}

function renderHistoryList(sessions) {
    historyList.innerHTML = '';
    
    const scrollWrapper = document.createElement('div');
    scrollWrapper.className = 'history-scroll-container';
    
    sessions.forEach(session => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.onclick = (e) => {
            if (!e.target.closest('.menu-dots') && !e.target.closest('.history-options')) {
                loadSession(session.id);
            }
        };
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'history-name';
        nameSpan.textContent = session.name;
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'history-time';
        timeSpan.textContent = new Date(session.timestamp).toLocaleString();
        
        const dots = document.createElement('span');
        dots.className = 'menu-dots';
        dots.innerHTML = '&#8942;';
        dots.onclick = (e) => toggleMenu(e, session.id);
        
        const optionsDiv = document.createElement('div');
        optionsDiv.id = `options-${session.id}`;
        optionsDiv.className = 'history-options';
        optionsDiv.innerHTML = `
            <button onclick="renameSession('${session.id}')">Rename</button>
            <button onclick="downloadSession('${session.id}')">Download</button>
            <button onclick="deleteSession('${session.id}')">Delete</button>
        `;
        
        div.appendChild(nameSpan);
        div.appendChild(timeSpan);
        div.appendChild(dots);
        div.appendChild(optionsDiv);
        
        scrollWrapper.appendChild(div);
    });
    
    historyList.appendChild(scrollWrapper);
}

function toggleMenu(e, sessionId) {
    e.stopPropagation();
    
    const menu = document.getElementById(`options-${sessionId}`);
    const isShown = menu.classList.contains('show');
    
    document.querySelectorAll('.history-options').forEach(el => el.classList.remove('show'));
    
    if (!isShown) {
        menu.classList.add('show');
    }
}

document.addEventListener('click', () => {
    document.querySelectorAll('.history-options').forEach(el => el.classList.remove('show'));
});

async function loadSession(sessionId) {
    try {
        const response = await fetch(`/api/history/${sessionId}`);
        const messages = await response.json();
        
        menuOverlay.classList.remove('active');
        backBtn.classList.remove('hidden');
        inputContainer.classList.add('hidden');
        statusIndicator.textContent = 'Viewing History';
        
        outputArea.innerHTML = '';
        messages.forEach(msg => {
            appendMessage(msg.content, msg.sender);
        });
        
    } catch (err) {
        console.error('Failed to load session:', err);
    }
}

async function renameSession(sessionId) {
    const newName = prompt("Enter new session name:");
    if (newName) {
        await fetch(`/api/history/${sessionId}/rename`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: newName})
        });
        fetchHistory();
    }
}

async function deleteSession(sessionId) {
    if (confirm("Are you sure you want to delete this chat?")) {
        await fetch(`/api/history/${sessionId}`, { method: 'DELETE' });
        fetchHistory();
    }
}

function downloadSession(sessionId) {
    window.location.href = `/api/history/${sessionId}/download`;
}
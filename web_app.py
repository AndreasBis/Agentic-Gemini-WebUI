import sys
import threading
import queue
import builtins
import json
import logging
import uuid
import io
import re
from typing import Any
from datetime import datetime
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file
)
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from main import AgenticGemini

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(
    app,
    cors_allowed_origins='*',
    async_mode='threading'
)

input_queue = queue.Queue()
output_lock = threading.Lock()
current_session_id = None

class ChatSession(db.Model):

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mode = db.Column(db.String(50))

class ChatMessage(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(36),
        db.ForeignKey('chat_session.id'),
        nullable=False
    )
    sender = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WebIO:

    def __init__(self):

        self.original_stdout = sys.stdout
        self.original_input = builtins.input
        self.suppress_patterns = [
            r'Max turns: \d+',
            r'Using default .*',
            r'to .*:',
            r'\(to .*\):',
            r'\[autogen\]',
            r'user_proxy',
            r'manager_agent',
            r'planner_agent',
            r'reviewer_agent',
            r'expert_agent',
            r'AFC is enabled',
            r'HTTP Request:',
            r'POST https://',
            r'GET /api/',
            r'HTTP/1.1',
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} - -',
            r'USING AUTO REPLY',
            r'Provide feedback'
        ]

    def _should_filter(self, text: str) -> bool:

        text = text.strip()
        if not text:
            return True

        for pattern in self.suppress_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def write(self, text: str) -> None:

        with output_lock:
            if text and not self._should_filter(text):
                socketio.emit('server_output', {'data': text})
                self._save_to_db('agent', text)

    def flush(self) -> None:

        pass

    def input(self, prompt: str = '') -> str:

        with output_lock:
            socketio.emit('request_input', {'prompt': prompt})

        return input_queue.get()

    def start_intercept(self) -> None:

        sys.stdout = self
        builtins.input = self.input

    def stop_intercept(self) -> None:

        sys.stdout = self.original_stdout
        builtins.input = self.original_input

    def _save_to_db(self, sender: str, content: str) -> None:

        if current_session_id:
            with app.app_context():
                msg = ChatMessage(
                    session_id=current_session_id,
                    sender=sender,
                    content=content
                )
                db.session.add(msg)
                db.session.commit()

web_io = WebIO()

@app.route('/')
def index() -> str:

    return render_template('index.html')

@app.route('/api/history')
def get_history() -> Any:

    sessions = ChatSession.query.order_by(ChatSession.timestamp.desc()).all()
    return jsonify([{
        'id': s.id,
        'name': s.name or f'Session {s.timestamp.strftime("%Y-%m-%d %H:%M")}',
        'timestamp': s.timestamp.isoformat(),
        'mode': s.mode
    } for s in sessions])

@app.route('/api/history/<session_id>')
def get_session_messages(session_id: str) -> Any:

    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.timestamp).all()
    return jsonify([{
        'sender': m.sender,
        'content': m.content,
        'timestamp': m.timestamp.isoformat()
    } for m in messages])

@app.route('/api/history/<session_id>', methods=['DELETE'])
def delete_session(session_id: str) -> Any:

    ChatMessage.query.filter_by(session_id=session_id).delete()
    ChatSession.query.filter_by(id=session_id).delete()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/history/<session_id>/rename', methods=['PUT'])
def rename_session(session_id: str) -> Any:

    data = request.get_json()
    new_name = data.get('name')
    session_entry = ChatSession.query.get(session_id)

    if session_entry:
        session_entry.name = new_name
        db.session.commit()
        return jsonify({'status': 'success'})

    return jsonify({'status': 'error'}), 404

@app.route('/api/history/<session_id>/download')
def download_session(session_id: str) -> Any:

    session_entry = ChatSession.query.get(session_id)
    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.timestamp).all()

    buffer = io.BytesIO()
    text_content = f'Chat Session: {session_entry.name}\n\n'
    for m in messages:
        text_content += f'[{m.sender.upper()}]:\n{m.content}\n\n{"-"*20}\n\n'

    buffer.write(text_content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'{session_entry.name or "session"}.txt',
        mimetype='text/plain'
    )

@socketio.on('user_input')
def handle_user_input(data: dict) -> None:

    user_text = data.get('message', '')
    web_io._save_to_db('user', user_text)
    input_queue.put(user_text)

@socketio.on('start_mode')
def handle_start_mode(data: dict) -> None:

    global current_session_id
    mode = data.get('mode')
    current_session_id = str(uuid.uuid4())

    with app.app_context():
        session_entry = ChatSession(
            id=current_session_id,
            mode=mode,
            name=f'Mode {mode} - {datetime.now().strftime("%H:%M")}'
        )
        db.session.add(session_entry)
        db.session.commit()

    thread = threading.Thread(target=run_agent_mode, args=(mode,))
    thread.daemon = True
    thread.start()

def run_agent_mode(mode_id: str) -> None:

    config_path = 'config_path.json'
    max_calls = 10

    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('google.ai.generativelanguage').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    try:
        with open(config_path, 'r') as f:
            app_config = json.load(f)

        config_list_path = app_config['config_path']
        gemini = AgenticGemini(
            config_path=config_list_path,
            max_calls=max_calls
        )

        web_io.start_intercept()

        logger = logging.getLogger()
        handler = logging.StreamHandler(web_io)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        if mode_id == '1':
            gemini.run_basic_code_agent()

        elif mode_id == '2':
            gemini.run_coder_reviewer_chat()

        elif mode_id == '3':
            gemini.run_group_chat_auto()

        elif mode_id == '4':
            gemini.run_human_in_the_loop_chat()

        elif mode_id == '5':
            gemini.run_tool_use_chat()

    except Exception as e:
        print(f'Error: {str(e)}')

    finally:
        web_io.stop_intercept()
        socketio.emit('session_ended')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    socketio.run(
        app,
        host='0.0.0.0',
        debug=True,
        port=5000
    )
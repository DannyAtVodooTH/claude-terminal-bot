"""
Web Interface - Simple terminal viewer and session management
"""

import json
import subprocess
from flask import Flask, render_template, jsonify, request
from pathlib import Path


class WebInterface:
    def __init__(self, config, session_manager, terminal_bridge):
        self.config = config
        self.session_manager = session_manager
        self.terminal_bridge = terminal_bridge
        
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Claude Bot Terminal</title>
                <style>
                    body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }
                    .terminal { background: #000; color: #00ff00; padding: 20px; border-radius: 5px; min-height: 400px; }
                    .session-list { margin-bottom: 20px; }
                    .session-item { display: inline-block; margin-right: 10px; padding: 5px 10px; background: #333; border-radius: 3px; cursor: pointer; }
                    .session-item.active { background: #007acc; }
                    pre { white-space: pre-wrap; margin: 0; }
                    .controls { margin-bottom: 20px; }
                    input, button { padding: 5px 10px; margin-right: 10px; }
                </style>
            </head>
            <body>
                <h1>Claude Bot Terminal</h1>
                
                <div class="controls">
                    <input type="text" id="sessionName" placeholder="Session name" />
                    <button onclick="createSession()">New Session</button>
                    <button onclick="refreshSessions()">Refresh</button>
                </div>
                
                <div class="session-list" id="sessions"></div>
                
                <div class="terminal" id="terminal">
                    <pre id="output">Select a session to view terminal output...</pre>
                </div>
                
                <div class="controls">
                    <input type="text" id="command" placeholder="Enter command..." onkeypress="handleKeyPress(event)" />
                    <button onclick="sendCommand()">Send</button>
                    <button onclick="startClaude()">Start Claude Code</button>
                </div>
                
                <script>
                let currentSession = null;
                
                function createSession() {
                    const name = document.getElementById('sessionName').value || 'web-session';
                    fetch('/api/sessions', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({name: name, topic: 'web'})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            refreshSessions();
                            document.getElementById('sessionName').value = '';
                        }
                    });
                }
                
                function refreshSessions() {
                    fetch('/api/sessions')
                    .then(response => response.json())
                    .then(sessions => {
                        const container = document.getElementById('sessions');
                        container.innerHTML = '';
                        sessions.forEach(session => {
                            const div = document.createElement('div');
                            div.className = 'session-item' + (session.id === currentSession ? ' active' : '');
                            div.textContent = session.id + ': ' + session.name;
                            div.onclick = () => selectSession(session.id);
                            container.appendChild(div);
                        });
                    });
                }
                
                function selectSession(sessionId) {
                    currentSession = sessionId;
                    refreshSessions();
                    getTerminalOutput();
                }
                
                function getTerminalOutput() {
                    if (!currentSession) return;
                    fetch(`/api/sessions/${currentSession}/output`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('output').textContent = data.output;
                    });
                }
                
                function sendCommand() {
                    const command = document.getElementById('command').value;
                    if (!command || !currentSession) return;
                    
                    fetch(`/api/sessions/${currentSession}/command`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command: command})
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('command').value = '';
                        setTimeout(getTerminalOutput, 500);
                    });
                }
                
                function startClaude() {
                    if (!currentSession) return;
                    fetch(`/api/sessions/${currentSession}/claude/start`, {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        setTimeout(getTerminalOutput, 1000);
                    });
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendCommand();
                    }
                }
                
                // Auto refresh output every 2 seconds
                setInterval(() => {
                    if (currentSession) getTerminalOutput();
                }, 2000);
                
                // Load sessions on page load
                refreshSessions();
                </script>
            </body>
            </html>
            '''

        @self.app.route('/api/sessions')
        def list_sessions():
            return jsonify(self.session_manager.list_sessions())

        @self.app.route('/api/sessions', methods=['POST'])
        def create_session():
            data = request.json
            name = data.get('name', 'web-session')
            topic = data.get('topic', 'web')
            
            try:
                session_id = self.session_manager.create_session(name, topic)
                return jsonify({'success': True, 'session_id': session_id})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/sessions/<session_id>/output')
        def get_output(session_id):
            sessions = {s['id']: s for s in self.session_manager.list_sessions()}
            if session_id not in sessions:
                return jsonify({'error': 'Session not found'})
            
            session = sessions[session_id]
            output = self.terminal_bridge.get_session_history(session, 100)
            return jsonify({'output': output})

        @self.app.route('/api/sessions/<session_id>/command', methods=['POST'])
        def send_command(session_id):
            data = request.json
            command = data.get('command', '')
            
            sessions = {s['id']: s for s in self.session_manager.list_sessions()}
            if session_id not in sessions:
                return jsonify({'error': 'Session not found'})
            
            session = sessions[session_id]
            result = self.terminal_bridge.execute_command(command, session)
            return jsonify({'result': result})

        @self.app.route('/api/sessions/<session_id>/claude/start', methods=['POST'])
        def start_claude(session_id):
            sessions = {s['id']: s for s in self.session_manager.list_sessions()}
            if session_id not in sessions:
                return jsonify({'error': 'Session not found'})
            
            session = sessions[session_id]
            result = self.terminal_bridge.start_claude_code(session)
            return jsonify({'result': result})

    def run(self, host='localhost', port=8080, debug=False):
        """Start the web interface."""
        self.app.run(host=host, port=port, debug=debug)


def main():
    """For testing the web interface standalone."""
    from session_manager import SessionManager
    from terminal_bridge import TerminalBridge
    
    # Mock config for testing
    config = {
        'sessions': {
            'base_dir': '~/sessions',
            'tmux_prefix': 'claude-session-'
        },
        'claude_code': {
            'executable': 'claude_code'
        }
    }
    
    session_manager = SessionManager(config['sessions'])
    terminal_bridge = TerminalBridge(config)
    
    web = WebInterface(config, session_manager, terminal_bridge)
    print("Starting web interface on http://localhost:8080")
    web.run(debug=True)


if __name__ == '__main__':
    main()

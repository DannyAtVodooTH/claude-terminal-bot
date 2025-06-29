"""
Session Manager - Handle terminal session lifecycle and persistence
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime


class SessionManager:
    def __init__(self, config):
        self.config = config
        self.base_dir = Path(config['base_dir'])
        self.base_dir.mkdir(exist_ok=True)
        
        # Track active sessions
        self.sessions = {}
        self.topic_sessions = {}  # Map Zulip topics to session IDs
        self.global_active_session = None  # Fallback for private messages
        
        # Load existing sessions
        self.load_sessions()

    def create_session(self, name, topic=None):
        """Create a new terminal session."""
        # Generate session ID
        session_id = self.generate_session_id()
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Create session structure
        (session_dir / "context").mkdir(exist_ok=True)
        
        # Session metadata
        session_data = {
            "id": session_id,
            "name": name,
            "working_dir": str(session_dir),  # Default to session dir
            "tmux_session": f"{self.config['tmux_prefix']}{session_id}",
            "claude_code_active": False,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "context_files": [],
            "environment": {},
            "topic": topic
        }
        
        # Save session config
        with open(session_dir / "session.json", 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Create tmux session
        tmux_name = session_data["tmux_session"]
        try:
            # First, try to kill any existing tmux session with the same name
            try:
                subprocess.run(["tmux", "kill-session", "-t", tmux_name], 
                             check=False, capture_output=True)
            except subprocess.CalledProcessError:
                pass  # Session didn't exist, that's fine
            
            # Now create the new tmux session
            subprocess.run([
                "tmux", "new-session", "-d", "-s", tmux_name,
                "-c", session_data["working_dir"]
            ], check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            # If it still fails, cleanup and raise
            session_dir.rmdir() if session_dir.exists() else None
            raise Exception(f"Failed to create tmux session: {e}")
        
        # Store in memory
        self.sessions[session_id] = session_data
        if topic:
            self.topic_sessions[topic] = session_id
        
        return session_id

    def switch_session(self, session_id, topic):
        """Switch active session for a topic."""
        if session_id not in self.sessions:
            return False
        
        self.topic_sessions[topic] = session_id
        self.global_active_session = session_id  # Set as global active too
        self.sessions[session_id]["last_active"] = datetime.now().isoformat()
        self.save_session(session_id)
        return True

    def get_current_session(self, topic):
        """Get the current active session for a topic."""
        session_id = self.topic_sessions.get(topic)
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        # Fallback to global active session for private messages
        if self.global_active_session and self.global_active_session in self.sessions:
            return self.sessions[self.global_active_session]
        
        return None

    def list_sessions(self):
        """List all active sessions."""
        return list(self.sessions.values())

    def sleep_session(self, session_id):
        """Put session to sleep (detach but keep running)."""
        if session_id not in self.sessions:
            return False
        
        # Session stays in tmux, just mark as sleeping
        self.sessions[session_id]["status"] = "sleeping"
        self.save_session(session_id)
        return True

    def kill_session(self, session_id):
        """Terminate a session completely."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        tmux_name = session["tmux_session"]
        
        # Kill tmux session
        try:
            subprocess.run(["tmux", "kill-session", "-t", tmux_name], check=True)
        except subprocess.CalledProcessError:
            pass  # Session might already be dead
        
        # Remove from memory
        del self.sessions[session_id]
        
        # Remove from topic mapping
        topic = session.get("topic")
        if topic and self.topic_sessions.get(topic) == session_id:
            del self.topic_sessions[topic]
        
        return True

    def set_working_directory(self, session_id, working_dir):
        """Change the working directory for a session."""
        if session_id not in self.sessions:
            return False
        
        working_dir = os.path.expanduser(working_dir)
        if not os.path.exists(working_dir):
            return False
        
        self.sessions[session_id]["working_dir"] = working_dir
        
        # Update tmux session working directory
        tmux_name = self.sessions[session_id]["tmux_session"]
        try:
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, f"cd {working_dir}", "Enter"
            ], check=True)
        except subprocess.CalledProcessError:
            pass
        
        self.save_session(session_id)
        return True

    def add_context_file(self, session_id, filename):
        """Add a file to session context."""
        if session_id not in self.sessions:
            return False
        
        context_files = self.sessions[session_id]["context_files"]
        if filename not in context_files:
            context_files.append(filename)
            self.save_session(session_id)
        
        return True

    def generate_session_id(self):
        """Generate a unique session ID."""
        existing_ids = set(self.sessions.keys())
        for i in range(1, 1000):
            session_id = f"{i:03d}"
            if session_id not in existing_ids:
                return session_id
        raise Exception("Too many sessions")

    def load_sessions(self):
        """Load existing sessions from disk."""
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            session_file = session_dir / "session.json"
            if not session_file.exists():
                continue
            
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Validate required fields
                if 'id' not in session_data:
                    print(f"Session file missing 'id' field: {session_file}")
                    continue
                
                session_id = session_data["id"]
                self.sessions[session_id] = session_data
                
                # Check if tmux session is still alive
                tmux_name = session_data["tmux_session"]
                try:
                    subprocess.run([
                        "tmux", "has-session", "-t", tmux_name
                    ], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    # Tmux session is dead, recreate it
                    self.recreate_tmux_session(session_data)
                
                # Restore topic mapping
                topic = session_data.get("topic")
                if topic:
                    self.topic_sessions[topic] = session_id
                
                # Set first session as global active if none set
                if not self.global_active_session:
                    self.global_active_session = session_id
                    
            except Exception as e:
                print(f"Failed to load session {session_dir}: {e}")

    def recreate_tmux_session(self, session_data):
        """Recreate a tmux session for an existing session."""
        tmux_name = session_data["tmux_session"]
        working_dir = session_data["working_dir"]
        
        try:
            subprocess.run([
                "tmux", "new-session", "-d", "-s", tmux_name,
                "-c", working_dir
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to recreate tmux session {tmux_name}: {e}")

    def save_session(self, session_id):
        """Save session data to disk."""
        if session_id not in self.sessions:
            return
        
        session_data = self.sessions[session_id]
        session_dir = self.base_dir / session_id
        
        with open(session_dir / "session.json", 'w') as f:
            json.dump(session_data, f, indent=2)

    def get_session_dir(self, session_id):
        """Get the session directory path."""
        return self.base_dir / session_id

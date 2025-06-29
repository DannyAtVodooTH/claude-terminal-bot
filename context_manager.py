"""
Context Manager - Handle file uploads and session context
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime


class ContextManager:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)

    def upload_file(self, session_id, file_path, content=None):
        """Upload a file to session context."""
        session_dir = self.base_dir / session_id
        context_dir = session_dir / "context"
        
        if not context_dir.exists():
            context_dir.mkdir(parents=True)
        
        # Get filename from path
        filename = os.path.basename(file_path)
        target_path = context_dir / filename
        
        try:
            if content:
                # Write content directly
                with open(target_path, 'w') as f:
                    f.write(content)
            elif os.path.exists(file_path):
                # Copy existing file
                shutil.copy2(file_path, target_path)
            else:
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            # Update session context files list
            self.update_context_list(session_id, filename)
            
            return f"File uploaded: {filename}"
            
        except Exception as e:
            return f"Upload failed: {str(e)}"

    def list_context_files(self, session_id):
        """List files in session context."""
        context_dir = self.base_dir / session_id / "context"
        
        if not context_dir.exists():
            return []
        
        files = []
        for file_path in context_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return files

    def get_context_file(self, session_id, filename):
        """Get content of a context file."""
        context_dir = self.base_dir / session_id / "context"
        file_path = context_dir / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def delete_context_file(self, session_id, filename):
        """Delete a file from session context."""
        context_dir = self.base_dir / session_id / "context"
        file_path = context_dir / filename
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            self.remove_from_context_list(session_id, filename)
            return True
        except Exception:
            return False

    def clear_context(self, session_id):
        """Clear all files from session context."""
        context_dir = self.base_dir / session_id / "context"
        
        if not context_dir.exists():
            return True
        
        try:
            for file_path in context_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            
            # Clear context list in session
            self.clear_context_list(session_id)
            return True
            
        except Exception:
            return False

    def create_symlink(self, session_id, target_dir):
        """Create symlink to working directory."""
        session_dir = self.base_dir / session_id
        link_path = session_dir / "working_dir"
        
        # Remove existing symlink if it exists
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        
        try:
            target_path = Path(target_dir).expanduser().resolve()
            link_path.symlink_to(target_path)
            return True
        except Exception:
            return False

    def get_project_context(self, working_dir, project_files):
        """Read project context files from working directory."""
        context = {}
        working_path = Path(working_dir)
        
        for filename in project_files:
            file_path = working_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        context[filename] = f.read()
                except Exception as e:
                    context[filename] = f"Error reading {filename}: {str(e)}"
        
        return context

    def update_context_list(self, session_id, filename):
        """Update the context files list in session config."""
        session_file = self.base_dir / session_id / "session.json"
        
        if not session_file.exists():
            return
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            context_files = session_data.get("context_files", [])
            if filename not in context_files:
                context_files.append(filename)
                session_data["context_files"] = context_files
                session_data["last_active"] = datetime.now().isoformat()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to update context list: {e}")

    def remove_from_context_list(self, session_id, filename):
        """Remove file from context list in session config."""
        session_file = self.base_dir / session_id / "session.json"
        
        if not session_file.exists():
            return
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            context_files = session_data.get("context_files", [])
            if filename in context_files:
                context_files.remove(filename)
                session_data["context_files"] = context_files
                session_data["last_active"] = datetime.now().isoformat()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to remove from context list: {e}")

    def clear_context_list(self, session_id):
        """Clear context files list in session config."""
        session_file = self.base_dir / session_id / "session.json"
        
        if not session_file.exists():
            return
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            session_data["context_files"] = []
            session_data["last_active"] = datetime.now().isoformat()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to clear context list: {e}")

    def save_command_history(self, session_id, command, output):
        """Save command and output to session history."""
        session_dir = self.base_dir / session_id
        history_file = session_dir / "history.log"
        
        try:
            timestamp = datetime.now().isoformat()
            entry = {
                "timestamp": timestamp,
                "command": command,
                "output": output
            }
            
            with open(history_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
                
        except Exception as e:
            print(f"Failed to save command history: {e}")

    def get_command_history(self, session_id, limit=50):
        """Get recent command history from session."""
        session_dir = self.base_dir / session_id
        history_file = session_dir / "history.log"
        
        if not history_file.exists():
            return []
        
        try:
            entries = []
            with open(history_file, 'r') as f:
                lines = f.readlines()
                # Get last N lines
                for line in lines[-limit:]:
                    entries.append(json.loads(line.strip()))
            
            return entries
            
        except Exception as e:
            print(f"Failed to read command history: {e}")
            return []

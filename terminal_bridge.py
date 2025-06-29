"""
Terminal Bridge - Execute commands in session context and manage Claude Code
"""

import os
import subprocess
import asyncio
import time
from pathlib import Path


class TerminalBridge:
    def __init__(self, config):
        self.config = config
        self.claude_config = config.get('claude_code', {})
        self.security_config = config.get('security', {})

    def execute_command(self, command, session):
        """Execute a command in the session's tmux session."""
        try:
            # Security check
            if not self.is_command_allowed(command):
                return f"Command blocked for security: {command}"
            
            tmux_name = session["tmux_session"]
            
            # Check if Claude Code is active and command should go there
            if session.get("claude_code_active") and not command.startswith('/'):
                return self.send_to_claude_code(command, session)
            
            # Clear any pending input first
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, "C-c"
            ], check=False, capture_output=True)
            time.sleep(0.1)
            
            # Execute command in tmux session
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, command, "Enter"
            ], check=True, capture_output=True)
            
            # Wait for command to execute
            time.sleep(1.0)  # Increased wait time
            
            # Capture only recent output (last 10 lines)
            result = subprocess.run([
                "tmux", "capture-pane", "-t", tmux_name, "-S", "-10", "-p"
            ], capture_output=True, text=True, check=True)
            
            # Process output to remove duplicates and clean up
            lines = result.stdout.strip().split('\n')
            
            # Find the command execution in the output
            command_found = False
            output_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip lines that are just the command being typed
                if line == command:
                    command_found = True
                    continue
                    
                # Skip prompt lines before command
                if not command_found and ('$' in line or '>' in line):
                    continue
                    
                # Include actual output after command
                if command_found:
                    output_lines.append(line)
            
            # If no specific output found, get last few meaningful lines
            if not output_lines:
                meaningful_lines = []
                for line in reversed(lines):
                    line = line.strip()
                    if line and line != command and not line.endswith('$'):
                        meaningful_lines.append(line)
                        if len(meaningful_lines) >= 3:
                            break
                output_lines = list(reversed(meaningful_lines))
            
            # Limit output length
            if len(output_lines) > 15:
                output_lines = output_lines[:10] + ["... (output truncated) ..."] + output_lines[-3:]
            
            return '\n'.join(output_lines) if output_lines else f"Command '{command}' executed (no output)"
            
        except subprocess.CalledProcessError as e:
            return f"Command execution failed: {e}"
        except Exception as e:
            return f"Error: {str(e)}"

    def send_to_claude_code(self, message, session):
        """Send message directly to Claude Code if it's running."""
        try:
            tmux_name = session["tmux_session"]
            
            # Send message to Claude Code
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, message, "Enter"
            ], check=True, capture_output=True)
            
            # Wait for Claude Code response
            time.sleep(2.0)  # Increased wait time
            
            # Capture output - get more lines for Claude Code
            result = subprocess.run([
                "tmux", "capture-pane", "-t", tmux_name, "-S", "-30", "-p"
            ], capture_output=True, text=True, check=True)
            
            # Process Claude Code output
            lines = result.stdout.strip().split('\n')
            
            # Find Claude Code response (after the command)
            output_lines = []
            found_command = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip until we find our command
                if message.lower() in line.lower():
                    found_command = True
                    continue
                    
                # Collect response after command
                if found_command:
                    # Skip empty prompt lines
                    if not line.endswith('$') and not line.startswith('│'):
                        output_lines.append(line)
            
            # If no specific output, get recent meaningful content
            if not output_lines:
                meaningful_lines = []
                for line in reversed(lines[-20:]):  # Last 20 lines
                    line = line.strip()
                    if line and not line.endswith('$'):
                        meaningful_lines.append(line)
                        if len(meaningful_lines) >= 10:
                            break
                output_lines = list(reversed(meaningful_lines))
            
            return '\n'.join(output_lines) if output_lines else f"Command '{message}' sent to Claude Code"
            
        except Exception as e:
            return f"Claude Code communication error: {str(e)}"

    def start_claude_code(self, session):
        """Start Claude Code in the session."""
        try:
            tmux_name = session["tmux_session"]
            working_dir = session["working_dir"]
            executable = self.claude_config.get("executable", "claude_code")
            
            # Check if Claude Code is available
            check_result = subprocess.run([
                "which", executable
            ], capture_output=True, text=True)
            
            if check_result.returncode != 0:
                return f"❌ Claude Code not found. Please install it first:\n" \
                       f"Visit: https://claude.ai/claude-code for installation instructions\n" \
                       f"Or update config.yaml with correct executable path"
            
            # Start Claude Code
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, f"cd {working_dir} && {executable}", "Enter"
            ], check=True)
            
            # Wait a bit for Claude to load
            time.sleep(2.0)
            
            # Handle trust prompt automatically by pressing Enter (Yes, proceed)
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, "Enter"
            ], check=True)
            
            # Wait for Claude Code to fully start
            time.sleep(3.0)
            
            # Check if it's running by looking for a prompt change
            result = subprocess.run([
                "tmux", "capture-pane", "-t", tmux_name, "-S", "-5", "-p"
            ], capture_output=True, text=True, check=True)
            
            # Mark as active in session
            session["claude_code_active"] = True
            
            # Auto-load project context if enabled
            if self.claude_config.get("auto_context", False):
                self.load_project_context(session)
            
            return f"✅ Claude Code started successfully in session {session['id']}\n" \
                   f"📁 Working directory: {working_dir}\n" \
                   f"🤖 Ready for AI-assisted development!"
            
        except Exception as e:
            return f"❌ Failed to start Claude Code: {str(e)}\n" \
                   f"💡 Try: 'which claude_code' to check if it's installed"

    def stop_claude_code(self, session):
        """Stop Claude Code in the session."""
        try:
            tmux_name = session["tmux_session"]
            
            # Send exit command to Claude Code
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, "exit", "Enter"
            ], check=True)
            
            time.sleep(1.0)
            
            # Send Ctrl+C just in case
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, "C-c"
            ], check=True)
            
            session["claude_code_active"] = False
            
            return "Claude Code stopped"
            
        except Exception as e:
            return f"Error stopping Claude Code: {str(e)}"

    def get_claude_code_status(self, session):
        """Check if Claude Code is running in the session."""
        if not session.get("claude_code_active"):
            return "Claude Code is not active"
        
        try:
            tmux_name = session["tmux_session"]
            
            # Check tmux session is alive
            subprocess.run([
                "tmux", "has-session", "-t", tmux_name
            ], check=True, capture_output=True)
            
            return "Claude Code is active"
            
        except subprocess.CalledProcessError:
            session["claude_code_active"] = False
            return "Claude Code session appears to be dead"

    def load_project_context(self, session):
        """Load project context files into Claude Code."""
        try:
            working_dir = Path(session["working_dir"])
            project_files = self.claude_config.get("project_files", [])
            
            for filename in project_files:
                file_path = working_dir / filename
                if file_path.exists():
                    # Send context load command to Claude Code
                    self.send_to_claude_code(f"@{file_path}", session)
                    time.sleep(0.5)
            
        except Exception as e:
            print(f"Failed to load project context: {e}")

    def is_command_allowed(self, command):
        """Check if command is allowed based on security settings."""
        if not self.security_config:
            return True
        
        # Check blocked commands
        blocked = self.security_config.get("blocked_commands", [])
        for blocked_cmd in blocked:
            if blocked_cmd in command:
                return False
        
        # Check allowed commands (if list exists, must be in it)
        allowed = self.security_config.get("allowed_commands", [])
        if allowed:
            cmd_start = command.split()[0] if command.split() else ""
            if cmd_start not in allowed:
                return False
        
        return True

    def get_session_history(self, session, lines=50):
        """Get command history from the session."""
        try:
            tmux_name = session["tmux_session"]
            
            # Capture more lines from tmux history
            result = subprocess.run([
                "tmux", "capture-pane", "-t", tmux_name, "-S", f"-{lines}", "-p"
            ], capture_output=True, text=True, check=True)
            
            return result.stdout.strip()
            
        except Exception as e:
            return f"Failed to get history: {str(e)}"

    def send_keys(self, session, keys):
        """Send specific key combinations to the session."""
        try:
            tmux_name = session["tmux_session"]
            
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_name, keys
            ], check=True)
            
            return "Keys sent successfully"
            
        except Exception as e:
            return f"Failed to send keys: {str(e)}"
